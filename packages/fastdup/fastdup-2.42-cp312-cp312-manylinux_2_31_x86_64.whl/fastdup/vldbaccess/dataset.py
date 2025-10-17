import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

import sqlalchemy as sa

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fastdup.vl.common import logging_init
from fastdup.vl.utils.useful_decorators import log_exception_with_args, timed
from fastdup.vldbaccess import sql_template_utils
from fastdup.vldbaccess.base import (
    BaseDB, DatasetSourceType, SampleDataset, DatasetStatus, AccessOperation, SeverityCount, Severity
)
from fastdup.vldbaccess import image_embeddings
from fastdup.vldbaccess.connection_manager import get_session, get_async_session, get_engine, get_engine_dialect
from fastdup.vldbaccess.models.dataset import Dataset, DatasetCounters
from fastdup.vldbaccess.sql_template_utils import QueryModule

logger = logging_init.get_vl_logger(__name__)


class DatasetDB(BaseDB):

    @staticmethod
    @log_exception_with_args
    def grant_access(dataset_id: UUID, user_id: UUID, ops: List[AccessOperation]):
        with get_session(autocommit=True) as session:
            DatasetDB._grant_access(session, dataset_id, user_id, ops)

    @staticmethod
    @log_exception_with_args
    def remove_access(dataset_id: UUID, user_id: UUID, ops: List[AccessOperation]):
        with get_session(autocommit=True) as session:
            DatasetDB._remove_access(session, dataset_id, user_id, ops)

    @staticmethod
    def flat_partition_name(dataset_id: UUID):
        return f"flat_similarity_clusters_{str(dataset_id).replace('-', '_')}"

    @staticmethod
    @log_exception_with_args
    def remove_partition(dataset_id: UUID, session: Session):
        partition_name = DatasetDB.flat_partition_name(dataset_id)
        try:
            # detach and drop flat partition if exists
            partition_exists: int = session.execute(
                sa.text('SELECT count(*) '
                        'FROM pg_catalog.pg_inherits '
                        'WHERE inhrelid::regclass::text=:partition_name'),
                {"partition_name": partition_name}
            ).one()[0]
            if partition_exists:
                session.execute(sa.text(f'ALTER TABLE flat_similarity_clusters DETACH PARTITION {partition_name};'))
                session.execute(sa.text(f'DROP TABLE {partition_name};'))
        except Exception as e:
            logger.exception(e)
            raise e

    @staticmethod
    @log_exception_with_args
    @timed
    def _remove_dataset(dataset_id: UUID, session: Session):
        ctx = {"dataset_id": dataset_id, }
        try:
            # remove access
            session.execute(
                sa.text('DELETE FROM access WHERE subject_id = :dataset_id'), ctx)
            # remove artifacts
            for table_name in [
                "dataset_issues", "label_categories", "labels", "clusters", "objects", "objects_to_images",
                "images_to_clusters", "images_to_similarity_clusters", "image_issues", "images"
            ]:
                session.execute(
                    sa.text(f'DELETE FROM "{table_name}" WHERE dataset_id = :dataset_id'), ctx)
            # remove dataset
            session.execute(
                sa.text('DELETE FROM datasets WHERE id = :dataset_id'), ctx)
            # detach and drop flat partition if exists
            if session.bind.dialect.name == 'postgresql':
                with session.begin(nested=True):
                    DatasetDB.remove_partition(dataset_id, session)
            session.commit()
            image_embeddings.get_image_embeddings_service(
                get_engine(), dataset_id
            ).cleanup()
        except Exception as e:
            logger.exception(e)
            raise e

    @staticmethod
    @log_exception_with_args
    def create(
            created_by: UUID,
            owned_by: str,
            display_name: str,
            preview_uri: str,
            source_uri: str,
            source_type: DatasetSourceType,
            description: str = '',
            filename: Optional[str] = None,
            sample: Optional[SampleDataset] = None,
            status: DatasetStatus = DatasetStatus.UPLOADING,
            score: int = -1,
            n_images: int = -1,
            n_objects: int = -1,
            n_clusters: int = -1,
            n_videos: int = -1,
            n_video_frames: int = -1,
            size_bytes: int = -1,
            deleted: bool = False,
            dataset_id: Optional[UUID] = None,
    ) -> Dataset:
        with get_session(autocommit=True) as session:
            if dataset_id:
                DatasetDB._remove_dataset(dataset_id, session)  # remove any existing dataset
            else:
                dataset_id = uuid.uuid1()

            ctx = {
                'dataset_id': dataset_id, 'created_by': created_by, 'owned_by': owned_by,
                'display_name': display_name, 'description': description, 'preview_uri': preview_uri,
                'source_uri': source_uri, 'source_type': source_type.name, 'filename': filename,
                'sample': None if sample is None else sample.name, 'status': status.name,
                'score': score, 'n_images': n_images, 'n_objects': n_objects, 'n_clusters': n_clusters,
                'n_videos': n_videos, 'n_video_frames': n_video_frames, 'size_bytes': size_bytes, 'deleted': deleted
            }
            row = session.execute(sa.text("""
                INSERT INTO
                    datasets (
                        id,
                        created_by,
                        owned_by,
                        display_name,
                        description,
                        preview_uri,
                        source_uri,
                        source_type,
                        filename,
                        sample,
                        status,
                        score,
                        n_images,
                        n_objects,
                        n_clusters,
                        n_videos,
                        n_video_frames,
                        size_bytes,
                        deleted
                        )
                VALUES
                    (
                    :dataset_id, 
                    :created_by, 
                    :owned_by, 
                    :display_name, 
                    :description, 
                    :preview_uri, 
                    :source_uri,
                    :source_type, 
                    :filename, 
                    :sample, 
                    :status, 
                    :score, 
                    :n_images, 
                    :n_objects, 
                    :n_clusters,
                    :n_videos, 
                    :n_video_frames, 
                    :size_bytes, 
                    :deleted)
                RETURNING
                    *;
                """), ctx).mappings().one()
            # session.commit()
            dataset: Dataset = Dataset.from_dict_row(row)
            DatasetDB._grant_access_to_group(session, dataset_id, 'administrators', [AccessOperation.MANAGE_ACCESS])
            DatasetDB._grant_access(session, dataset.dataset_id, created_by,
                                    [AccessOperation.READ, AccessOperation.LIST, AccessOperation.UPDATE,
                                     AccessOperation.DELETE])
            system_user_id: UUID = DatasetDB._get_system_user_id(session)
            if created_by != system_user_id:
                DatasetDB._grant_access(session, dataset.dataset_id, system_user_id,
                                        [AccessOperation.READ, AccessOperation.LIST, AccessOperation.UPDATE])
            if sample == SampleDataset.SAMPLE:
                DatasetDB._grant_access_to_all(session, dataset.dataset_id, [AccessOperation.READ])
            if sample == SampleDataset.DEFAULT_SAMPLE:
                DatasetDB._grant_access_to_all(session, dataset.dataset_id,
                                               [AccessOperation.READ, AccessOperation.LIST])

        return dataset

    @staticmethod
    @log_exception_with_args
    def update(
            dataset_id: UUID,
            **ctx
    ) -> Optional[Dataset]:
        table_cols = [
            "owned_by", "display_name", "description", "preview_uri", "source_uri", "source_type",
            "filename", "status", "score", "n_images", "n_objects", "n_clusters",
            "n_videos", "n_video_frames", "size_bytes", "progress", "fatal_error_msg",
            "pipeline_commit_id", "created_at", "media_embeddings", "media_embeddings_cosine_distance"
        ]
        if any([col not in table_cols for col in ctx]):
            raise KeyError(f"invalid update dataset column {ctx.keys()}")

        query = f"UPDATE datasets SET {','.join([f'{k} = :{k}' for k in ctx])} where id=:dataset_id"

        with get_session(autocommit=True) as session:
            session.execute(
                sa.text(query),
                ctx | {"dataset_id": dataset_id}
            )

        DatasetDB._handle_dataset_status_event(dataset_id, ctx)

        return None

    @staticmethod
    @log_exception_with_args
    def get_by_id(dataset_id: UUID, user_id: UUID, include_deleted: bool = False) -> Optional[Dataset]:
        with get_session() as session:
            deletion_status: list[bool] = [False]
            if include_deleted:
                deletion_status.append(True)
            row = session.execute(sa.text("""
                SELECT
                    *
                FROM
                    datasets 
                WHERE
                    id = :dataset_id
                    AND deleted = ANY(:deletion_status)
                ;"""), {"dataset_id": dataset_id, "user_id": user_id,
                        "deletion_status": deletion_status}).mappings().one_or_none()
            if not row:
                return None

            severity_distribution = DatasetDB._get_severity_distribution(dataset_id, row['n_images'], session)

        return Dataset.from_dict_row(row, severity_distribution)

    @staticmethod
    @log_exception_with_args
    async def get_by_id_async(
            session: AsyncSession, dataset_id: UUID, user_id: UUID, include_deleted: bool = False
    ) -> Optional[Dataset]:
        deletion_status: list[bool] = [False]
        if include_deleted:
            deletion_status.append(True)
        row = (await session.execute(sa.text("""
            SELECT
                *
            FROM
                datasets 
            WHERE
                id = :dataset_id
                AND deleted = ANY(:deletion_status)
            ;"""), {"dataset_id": dataset_id, "user_id": user_id,
                    "deletion_status": deletion_status})).mappings().one_or_none()
        if not row:
            return None

        severity_distribution = await DatasetDB.get_severity_distribution_async(
            session=session, dataset_id=dataset_id, total_count=row['n_images'])

        return Dataset.from_dict_row(row, severity_distribution)

    @staticmethod
    @log_exception_with_args
    @timed
    async def get_by_user_id(user_id: UUID) -> List[Dataset]:
        res: List[Dataset] = []
        async with get_async_session() as session:
            query_result = await session.execute(sa.text("""
            SELECT
                *
            FROM
                datasets 
            WHERE
                id in (SELECT object_id FROM access WHERE subject_id = :user_id AND operation = 'LIST')
                AND NOT deleted
            ;"""), {"user_id": user_id, })
            rows = query_result.mappings().all()
            severity_distribution_tasks = [
                DatasetDB.get_severity_distribution_async(row['id'], row['n_images'], session)
                for row in rows
            ]
            severity_distribution = await asyncio.gather(*severity_distribution_tasks)
            for row, severity_distribution in zip(rows, severity_distribution):
                res.append(Dataset.from_dict_row(
                    row, severity_distribution=severity_distribution)
                )

        return res

    @staticmethod
    @log_exception_with_args
    async def get_pvlds() -> List[Dataset]:
        res: List[Dataset] = []
        async with get_async_session() as session:
            query_result = await session.execute(sa.text("""
            SELECT
                *
            FROM
                datasets 
            WHERE
                sample in (:s, :ds)
                AND NOT deleted
            ;"""), {"s": SampleDataset.SAMPLE, "ds": SampleDataset.DEFAULT_SAMPLE})
            rows = query_result.mappings().all()
            for row in rows:
                severity_distribution = await DatasetDB.get_severity_distribution_async(
                    row['id'], row['n_images'], session)
                res.append(Dataset.from_dict_row(row, severity_distribution=severity_distribution))

        return res

    @staticmethod
    @log_exception_with_args
    def get_unlisted_by_user_id(user_id: UUID) -> List[Dataset]:
        with get_session() as session:
            rows = session.execute(sa.text("""
                SELECT
                    *
                FROM
                    datasets 
                WHERE
                    id NOT IN (SELECT object_id FROM access WHERE subject_id = :user_id AND operation = 'LIST')
                    AND id IN (SELECT object_id FROM access WHERE subject_id = :user_id AND operation = 'READ')
                    AND NOT deleted
                ;"""), {"user_id": user_id}).mappings().all()

        return [Dataset.from_dict_row(row) for row in rows]

    @staticmethod
    @log_exception_with_args
    def _get_severity_distribution(
            dataset_id: UUID,
            total_count: int,
            session: Session,
    ) -> List[SeverityCount]:
        rows = session.execute(sa.text("""
            SELECT severity, sum(n_images) + sum(n_objects)
            FROM dataset_issues, issue_type, clusters
            WHERE
                dataset_issues.dataset_id = :dataset_id
                AND dataset_issues.dataset_id = clusters.dataset_id
                AND dataset_issues.type_id = issue_type.id
                AND dataset_issues.cluster_id = clusters.id
            GROUP BY severity
            ORDER BY severity;
            """), {"dataset_id": dataset_id}
                               ).all()

        res: List[SeverityCount] = []
        sev_count: SeverityCount
        for sev in Severity:
            sev_count = SeverityCount(severity=sev, n_images=0)
            res.append(sev_count)
            for row in rows:
                if row[0] == sev.value:
                    sev_count.n_images = row[1]
                    sev_count.percentage_relative_to(total_count)
        return res

    @staticmethod
    @log_exception_with_args
    def get_severity_distribution(
            dataset_id: UUID,
            total_count: int,
    ) -> List[SeverityCount]:
        with get_session() as session:
            return DatasetDB._get_severity_distribution(dataset_id, total_count, session)

    @staticmethod
    @log_exception_with_args
    def delete(dataset_id: UUID, user_id: UUID) -> bool:
        with get_session(autocommit=True) as session:
            session.execute(sa.text("""
                UPDATE
                    datasets
                SET
                    deleted = true
                WHERE
                    id = :dataset_id
                    AND id in (SELECT object_id FROM access WHERE subject_id = :user_id AND operation = 'READ')
                ;"""), {"dataset_id": dataset_id, "user_id": user_id})
        return True

    @staticmethod
    def get_all_datasets() -> List[Dataset]:
        res: List[Dataset] = []
        with get_session() as session:
            rows = session.execute(sa.text("""SELECT * FROM datasets ;""")).mappings().all()

            for row in rows:
                res.append(Dataset.from_dict_row(row))

        return res

    @staticmethod
    @log_exception_with_args
    async def get_severity_distribution_async(
            dataset_id: UUID,
            total_count: int,
            session: AsyncSession,
    ) -> List[SeverityCount]:
        # TODO: duplicate method, replace non async method when possible
        query_result = await session.execute(sa.text("""
                SELECT severity, sum(n_images) + sum(n_objects)
                FROM dataset_issues, issue_type, clusters
                WHERE
                    dataset_issues.dataset_id = :dataset_id
                    AND dataset_issues.dataset_id = clusters.dataset_id
                    AND dataset_issues.type_id = issue_type.id
                    AND dataset_issues.cluster_id = clusters.id
                GROUP BY severity
                ORDER BY severity;
                """), {"dataset_id": dataset_id}
                                             )
        rows = query_result.all()
        res: List[SeverityCount] = []
        sev_count: SeverityCount
        for sev in Severity:
            sev_count = SeverityCount(severity=sev, n_images=0)
            res.append(sev_count)
            for row in rows:
                if row[0] == sev.value:
                    sev_count.n_images = row[1]
                    sev_count.percentage_relative_to(total_count)
        return res

    @staticmethod
    def counters(dataset_id: UUID) -> DatasetCounters:
        ctx = {"dataset_id": dataset_id}
        with get_session() as session:
            n_images = session.execute(sa.text(
                "SELECT COUNT(*) FROM images WHERE dataset_id=:dataset_id"), ctx
            ).one()[0]
            n_objects = session.execute(sa.text(
                "SELECT COUNT(*) FROM objects_to_images WHERE dataset_id=:dataset_id"), ctx
            ).fetchone()[0]
            n_videos = session.execute(sa.text(
                "SELECT COUNT(DISTINCT metadata->>'video') FROM images WHERE dataset_id=:dataset_id"),
                ctx
            ).fetchone()[0]
            n_frames = session.execute(sa.text(
                "SELECT COUNT(*) FROM images WHERE metadata->>'video' IS NOT NULL AND dataset_id=:dataset_id"),
                ctx
            ).fetchone()[0]
        return DatasetCounters(
            n_images=n_images,
            n_objects=n_objects,
            n_videos=n_videos,
            n_frames=n_frames
        )

    @staticmethod
    def generate_unique_display_name(user_id: UUID) -> str:
        if get_engine_dialect() == 'duckdb':
            raise NotImplementedError
        sequence_name = f'ds_name_seq_{user_id}'.replace('-', '_')
        with get_session(autocommit=True) as session:
            session.execute(sa.text(f'CREATE SEQUENCE IF NOT EXISTS {sequence_name};'))
            num = session.execute(
                sa.text('SELECT nextval(:sequence_name);'),
                {'sequence_name': sequence_name}
            ).fetchone()[0]
        return f'Dataset {num}'

    @staticmethod
    def has_events(dataset_id: UUID) -> bool:
        with get_session(autocommit=True) as session:
            events_exist = session.execute(sa.text(
                "SELECT 1 FROM events WHERE dataset_id=:dataset_id AND event_type != 'DatasetStatus' LIMIT 1"),
                {'dataset_id': dataset_id}
            ).one_or_none()
        return bool(events_exist)

    @staticmethod
    def update_thresholds_data(dataset_id: UUID):
        with get_session(autocommit=True) as session:
            query = sql_template_utils.render(
                QueryModule.DATASETS, "update_thresholds_data.jinja2",
                dataset_id=dataset_id
            )
            session.execute(sa.text(query), {"dataset_id": dataset_id})

    @staticmethod
    def update_dataset_status(
            session: Session,
            dataset_ids: list[UUID],
            status: DatasetStatus,
            error_msg: str
    ) -> None:
        session.execute(
            sa.text(
                "update datasets "
                "set status = :status, fatal_error_msg = :error_msg "
                "where id in ANY(:dataset_ids)"
            ), {"dataset_ids": dataset_ids, "status": status, "error_msg": error_msg}
        )

    @staticmethod
    def _get_stuck_datasets(
            session: Session,
            status: DatasetStatus,
            timeframe_offset_h: int = 3,
            limit: int = 1
    ) -> list[UUID]:
        ctx = {
            "status": status,
            "limit": limit,
            "timeframe_offset_h": timeframe_offset_h,
            "time_window": datetime.now() - timedelta(hours=timeframe_offset_h)
        }

        dataset_ids = session.execute(
            sa.text(
                "SELECT id FROM datasets "
                "WHERE status = :status "
                f"AND created_at < :time_window "
                "ORDER BY created_at ASC LIMIT :limit"
            ), ctx
        ).scalars().all()
        return dataset_ids

    @classmethod
    def process_stuck_datasets(cls):
        error_msg = 'Failed in {} dataset - pls email support@visual-layer.com'
        final_status = DatasetStatus.FATAL_ERROR
        limit = 1
        with get_session() as session:
            for initial_status, timeframe_offset in [
                (DatasetStatus.UPLOADING, 6),
            ]:
                dataset_ids = cls._get_stuck_datasets(
                    session, initial_status, timeframe_offset, limit
                )
                for dataset_id in dataset_ids:
                    logger.warning(
                        "Processing Stuck dataset: id %s status %s",
                        dataset_id, initial_status
                    )
                    cls.update(
                        dataset_id,
                        status=final_status,
                        fatal_error_msg=error_msg.format(repr(initial_status).lower())
                    )
