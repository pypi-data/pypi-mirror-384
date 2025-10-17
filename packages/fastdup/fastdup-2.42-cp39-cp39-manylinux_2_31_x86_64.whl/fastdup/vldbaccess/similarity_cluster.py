from typing import Dict, Optional, List, Tuple, Sequence
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import RowMapping

from fastdup.vl.common import logging_helpers, utils
from fastdup.vl.common.settings import Settings

from fastdup.vl.utils.useful_decorators import timed
from fastdup.vldbaccess.base import BaseDB
from fastdup.vldbaccess.connection_manager import get_async_session
from fastdup.vldbaccess.connection_manager import get_session
from fastdup.vldbaccess import create_flat_similarity_clusters
from fastdup.vldbaccess.data_exploration_models import MetadataSummarySection
from fastdup.vldbaccess.exploration_sqls import ExplorationContext
from fastdup.vldbaccess.models import similarity_cluster_view
from fastdup.vldbaccess.models.media import Media, MediaType
from fastdup.vldbaccess.models.similarity_cluster_view import SimilarityClusterView
from fastdup.vldbaccess.similarity_cluster_model import SimilarityCluster, SimilarityThreshold, SimilarityClusterType
from fastdup.vldbaccess import sql_template_utils
from fastdup.vldbaccess.sql_template_utils import QueryModule


class SimilarityClusterDB(BaseDB):
    BATCH_SIZE = 1000

    @staticmethod
    @timed
    def save_similarity_clusters(similarity_clusters: List[SimilarityCluster]):
        statement = """
            INSERT INTO similarity_clusters
            (id, dataset_id, cluster_type, display_name, n_images, n_objects, size_bytes, similarity_threshold, formed_by)
            VALUES
            (:id, :dataset_id, :type, :display_name, :n_images, :n_objects, :size_bytes, :similarity_threshold, :formed_by)
            ON CONFLICT (id) DO NOTHING
            RETURNING *;
        """
        for batch in utils.iter_batches(
                similarity_clusters, SimilarityClusterDB.BATCH_SIZE,
                func=lambda x: x.dict()
        ):
            SimilarityClusterDB.execute_batch_stmt(statement, batch)

    @staticmethod
    @timed(context_keys=["context.dataset_id"])
    async def similarity_clusters_by_dataset(
            context: ExplorationContext,
            max_previews=9
    ) -> Optional[List[SimilarityClusterView]]:
        async with get_async_session() as session:
            if context.page_number is None:
                context.page_number = 0
            offset: Optional[int] = Settings.CLUSTERS_PAGE_SIZE * context.page_number
            query = sql_template_utils.render(
                QueryModule.EXPLORATION, "exploration_query.jinja2",
                # flags
                offset=offset,
                page_size=Settings.CLUSTERS_PAGE_SIZE,
                # context
                max_previews=max_previews,
                **context.dict(),
            )
            with logging_helpers.log_sql_query_time(
                    __name__, "similarity_clusters_by_dataset", query, context.dict(), duration_seconds=0):
                cluster_rows: Sequence[RowMapping] = (
                    await session.execute(sa.text(query), context.dict())).mappings().all()
        clusters = SimilarityClusterView.from_row_list(cluster_rows)
        return clusters

    @classmethod
    async def get_media_as_cluster(
            cls,
            context: ExplorationContext,
            media_id: UUID,
    ) -> Optional[SimilarityClusterView]:
        clusters = await cls.get_similarity_clusters_for_entities(context, [media_id])
        if len(clusters):
            return clusters[0]
        return None

    @staticmethod
    @timed(context_keys=["context.dataset_id", "context.cluster_id"])
    async def get_similarity_cluster(context: ExplorationContext) -> Optional[SimilarityClusterView]:
        async with get_async_session() as session:
            query = sql_template_utils.render(QueryModule.EXPLORATION, "get_similarity_cluster.jinja2",
                page_size=Settings.CLUSTER_ENTITIES_PAGE_SIZE,
                **context.dict()
            )
            with logging_helpers.log_sql_query_time(
                    __name__, "get_similarity_cluster", query, context.dict(), duration_seconds=0):
                rows: Sequence[RowMapping] = (await session.execute(sa.text(query), context.dict())).mappings().all()

            query = sql_template_utils.render(
                QueryModule.EXPLORATION, "cluster_labels.jinja2", **context.dict()
            )
            with logging_helpers.log_sql_query_time(
                    __name__, "get_similarity_cluster_labels", query, context.dict(), duration_seconds=1):
                cluster_labels_rows: Sequence[RowMapping] = (
                    await session.execute(sa.text(query), context.dict())).mappings().all()

        if rows is None or len(rows) == 0:
            return None

        cluster = SimilarityClusterView.from_row_list(rows)[0]

        similarity_cluster_view.enrich_with_labels([cluster], cluster_labels_rows)

        return cluster

    @staticmethod
    @timed
    async def get_similarity_cluster_size(context: ExplorationContext) -> Optional[int]:
        query = sql_template_utils.template_to_sql(
            sql_template_utils.render(
                QueryModule.EXPLORATION, "cluster_size.jinja2", **context.dict()
            )
        )
        async with get_async_session() as session:
            qr = await session.execute(sa.text(query), context.dict())
            rows: Sequence[RowMapping] = qr.mappings().all()

        if rows is None or len(rows) == 0:
            return None

        return rows[0]['cnt']

    @staticmethod
    @timed
    async def get_similarity_cluster_count_for_dataset(context: ExplorationContext) -> Optional[int]:
        query = sql_template_utils.render(
            QueryModule.EXPLORATION, "get_cluster_count_for_dataset.jinja2", **context.dict()
        )
        async with get_async_session() as session:
            qr = await session.execute(sa.text(query), context.dict())
            rows: Sequence[RowMapping] = qr.mappings().all()

        if rows is None or len(rows) == 0:
            return None

        return rows[0]['cnt']

    @staticmethod
    async def get_dataset_similarity_thresholds(dataset_id: UUID) -> List[SimilarityThreshold]:
        async with get_async_session() as session:
            qr = await session.execute(sa.text(
                """
                SELECT DISTINCT
                    similarity_threshold
                FROM
                    similarity_clusters
                WHERE
                    dataset_id = :dataset_id
                ORDER BY
                    similarity_threshold
                """),
                {'dataset_id': dataset_id}
            )
            rows: Sequence[RowMapping] = qr.mappings().all()
        if not rows:
            return []

        return [SimilarityThreshold.from_str(row['similarity_threshold']) for row in rows]

    @staticmethod
    @timed
    def create_and_fill_partition(dataset_id: UUID):
        create_flat_similarity_clusters.create_and_fill_partition(dataset_id)

    @staticmethod
    async def get_similarity_data_by_ds_id(dataset_ids: List[UUID]) -> Dict[UUID, bool]:
        async with get_async_session() as session:
            rows = (await session.execute(
                sa.text("""
                SELECT
                    dataset_id
                FROM
                    similarity_clusters
                WHERE
                    dataset_id = ANY(:dataset_ids)
                GROUP BY
                    dataset_id
                """), {'dataset_ids': dataset_ids})).mappings().all()
            if not rows:
                rows = []
            return {dataset_id: dataset_id in [row['dataset_id'] for row in rows] for dataset_id in dataset_ids}

    @staticmethod
    @timed(context_keys=["dataset_id"])
    def exploration_stats(
            dataset_id: UUID,
            threshold: SimilarityThreshold = SimilarityThreshold.ZERO,
            label_filter: Optional[list[str]] = None,
    ) -> Tuple[dict[str, int], dict[UUID, dict[str, int]]]:
        with get_session() as session:
            rows: Sequence[RowMapping] = session.execute(sa.text(
                """
                WITH
                    limited_flat_similarities AS (
                        SELECT
                            *
                        FROM
                            flat_similarity_clusters
                        WHERE 
                            dataset_id = :dataset_id
                            AND similarity_threshold = :threshold
                        ORDER BY
                            (n_images + n_objects) DESC,
                            cluster_id,
                            preview_order
                        LIMIT
                            3200
                        ),                
                    count_by_cluster_id AS (
                        SELECT
                            cluster_id,
                            count(*) AS count_by_cluster_id
                        FROM
                            limited_flat_similarities
                        GROUP BY
                            cluster_id
                    ),
                    filtered_count_by_cluster_id AS (
                        SELECT
                            cluster_id,
                            count(*) AS filtered_count_by_cluster_id
                        FROM
                            limited_flat_similarities
                        WHERE 
                            (:disable_label_filter OR (labels && :label_filter))
                        GROUP BY
                            cluster_id
                    ),
                    count_by_type AS (
                        SELECT
                            COUNT(*) 
                                FILTER (WHERE cluster_type = 'IMAGES') AS total_images_count,
                            COUNT(*) 
                                FILTER (WHERE cluster_type = 'OBJECTS') AS total_objects_count
                        FROM 
                            limited_flat_similarities
                    ),
                    filtered_count_by_type AS (
                        SELECT 
                            count(*) 
                                FILTER (WHERE cluster_type = 'IMAGES') AS filtered_images_count,
                            count(*) 
                                FILTER (WHERE cluster_type = 'OBJECTS') AS filtered_objects_count
                        FROM 
                            limited_flat_similarities
                        WHERE 
                            (:disable_label_filter OR (labels && :label_filter))                            
                    ),                                        
                    clusters_count AS (
                        SELECT
                            COUNT(*) as clusters_count                            
                        FROM
                            count_by_cluster_id
                    ),
                    filtered_count AS (
                        SELECT 
                            count(*) AS filtered_clusters_count
                        FROM 
                            filtered_count_by_cluster_id
                    )
                    SELECT
                        count_by_cluster_id.cluster_id,
                        count_by_cluster_id.count_by_cluster_id,
                        filtered_count_by_cluster_id.filtered_count_by_cluster_id,
                        count_by_type.total_images_count,
                        count_by_type.total_objects_count,
                        filtered_count_by_type.filtered_images_count,
                        filtered_count_by_type.filtered_objects_count,                        
                        clusters_count.clusters_count,
                        filtered_count.filtered_clusters_count
                    FROM
                        count_by_cluster_id
                    LEFT JOIN
                        filtered_count_by_cluster_id ON 
                        count_by_cluster_id.cluster_id = filtered_count_by_cluster_id.cluster_id
                    CROSS JOIN
                        count_by_type, filtered_count_by_type, clusters_count, filtered_count
                    ORDER BY
                        filtered_count_by_cluster_id.filtered_count_by_cluster_id DESC NULLS LAST                    
                    """), {
                'dataset_id': dataset_id,
                'threshold': threshold,
                'disable_label_filter': label_filter is None or len(label_filter) == 0,
                'label_filter': label_filter,
            },
            ).mappings().all()
            global_counts = {
                "total_images_count": 0, "filtered_images_count": 0, "total_objects_count": 0,
                "filtered_objects_count": 0, "clusters_count": 0, "filtered_clusters_count": 0
            }
            if rows is None:
                rows = [global_counts]
            else:
                global_counts = {k: rows[0][k] for k in global_counts.keys()}
                rows = rows[:global_counts['filtered_clusters_count']]
            counts_by_cluster_id = {
                row['cluster_id']: {
                    "total": row['count_by_cluster_id'], "filtered": row['filtered_count_by_cluster_id']
                } for row in rows
            }
            return global_counts, counts_by_cluster_id

    @staticmethod
    @timed
    async def get_similarity_data_by_media_ids(media_ids: List[UUID]) -> Optional[List[Dict]]:
        async with get_async_session() as session:
            rows = (await session.execute(sa.text(
                """
                SELECT
                    *
                FROM
                    flat_similarity_clusters
                WHERE
                    image_or_object_id = ANY(:media_ids)
                ORDER BY
                    preview_order DESC;
                """), {'media_ids': media_ids})).mappings().all()
        if rows is None:
            return None
        return rows

    @staticmethod
    @timed(context_keys=["context.dataset_id", "context.cluster_id", "summary_section"])
    async def get_similarity_cluster_metadata_summary(
            context: ExplorationContext, summary_section=MetadataSummarySection.ALL) -> List[Dict]:
        query = sql_template_utils.render(
            QueryModule.EXPLORATION, "metadata_summary/metadata_summary.jinja2",
            summary_section=summary_section,
            MetadataSummarySection=MetadataSummarySection,
            **context.dict()
        )
        async with get_async_session() as session:
            with logging_helpers.log_sql_query_time(
                    __name__, "get_similarity_cluster_metadata_summary", query, context.dict(),
                    duration_seconds=1
            ):
                qr = await session.execute(sa.text(query), context.dict())
                rows: list[dict] = qr.mappings().all()
        return rows

    @staticmethod
    async def get_similarity_clusters_for_entities(
            context: ExplorationContext,
            entity_ids: List[UUID],
    ) -> list['SimilarityClusterView']:
        ctx = context.dict() | {'entity_ids': entity_ids}
        query = sql_template_utils.render(
            QueryModule.EXPLORATION, "get_similarity_clusters_for_entities.jinja2", **ctx,
        )
        async with get_async_session() as session:
            cluster_rows = (
                await session.execute(sa.text(query), ctx)).mappings().all()
        clusters = []
        for cluster_row in cluster_rows:
            cluster_list = SimilarityClusterView.from_row_list([cluster_row])
            cluster = cluster_list[0]
            cluster.labels = {label: 1 for label in (cluster_row["labels"] or []) + (cluster_row["vl_labels"] or [])}
            clusters.append(cluster)
        return clusters

    @staticmethod
    async def dataset_has_captions(dataset_id: UUID) -> bool:
        async with get_async_session() as session:
            rows: Sequence[RowMapping] = (await session.execute(sa.text(
                """
                SELECT
                    caption
                FROM
                    flat_similarity_clusters
                WHERE
                dataset_id = :dataset_id
                    AND caption IS NOT NULL
                    AND caption != ''
                LIMIT 
                    1;
                """), {'dataset_id': dataset_id})).mappings().all()
        if not rows:
            return False
        return True

    @staticmethod
    async def get_clusters_entities(dataset_id: UUID, cluster_ids: List[UUID]) -> List[Media]:
        async with get_async_session() as session:
            rows: Sequence[RowMapping] = (await session.execute(sa.text(
                """
                SELECT
                    *
                FROM
                    flat_similarity_clusters
                WHERE
                    cluster_id = ANY(:cluster_ids)
                AND
                    dataset_id = :dataset_id
                """
            ), {'cluster_ids': cluster_ids, 'dataset_id': dataset_id})).mappings().all()
            if not rows:
                return []
            return [Media.from_row_dict(row) for row in rows]

    @staticmethod
    async def get_query_media_as_cluster(dataset_id: UUID, media_id: UUID, context: ExplorationContext):
        async with get_async_session() as session:
            row = (await session.execute(
                sa.text(
                    "SELECT media_id, image_uri, bounding_box, filename FROM query_vector_embedding "
                    "WHERE dataset_id = :dataset_id AND media_id = :media_id"
                ), {"dataset_id": dataset_id, "media_id": media_id}
            )).mappings().one()
        cluster = SimilarityClusterView.from_dict_row({
            "cluster_type": SimilarityClusterType.IMAGES,
            "similarity_threshold": context.threshold,
            "cluster_id": media_id,
        })
        image_uri = row["image_uri"]
        media = Media(
            type=MediaType.IMAGE,
            media_id=media_id,
            media_uri=image_uri,
            media_thumb_uri=image_uri,
            bounding_box=row["bounding_box"],
            file_name=row["filename"]
        )
        cluster.previews.extend([media])
        return cluster
