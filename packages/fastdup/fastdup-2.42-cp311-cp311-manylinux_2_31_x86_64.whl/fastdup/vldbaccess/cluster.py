import uuid
from typing import Dict, Optional, List, NamedTuple
from uuid import UUID

import sqlalchemy as sa

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fastdup.vl.utils.useful_decorators import log_exception_with_args
from fastdup.vldbaccess.cluster_model import (
    ClusterType, ChildCluster, Cluster, ImageForLeafClusterView, ClusterOfImages,
    from_db_row, ClusterStats, ClusterOfObjects, ImageWithObject)
from fastdup.vldbaccess.connection_manager import get_session, get_async_session
from fastdup.vldbaccess.dataset import DatasetDB, Dataset
from fastdup.vldbaccess.image import LabelType
from fastdup.vldbaccess.label import LabelDal
from fastdup.vldbaccess.previews import get_previews


class Previews(NamedTuple):
    image_previews: Dict[UUID, List[str]]
    object_previews: Dict[UUID, List[str]]


class ClusterPath(BaseModel):
    type: str
    id: UUID
    display_name: str

    @staticmethod
    @log_exception_with_args
    def from_db_row(row: dict):
        return ClusterPath(
            type=row['type'],
            id=row['id'],
            display_name=row['display_name']
        )


class ClusterDB:

    @staticmethod
    @log_exception_with_args
    async def _get_root_cluster_by_child_cluster(
            dataset_id: UUID,
            cluster_id: UUID,
            user_id: UUID,
            session: AsyncSession,
    ) -> Optional[Cluster]:
        stmt = """
            WITH RECURSIVE cte AS (
                SELECT * FROM clusters WHERE clusters.id = :cluster_id
                UNION ALL
                SELECT clusters.* FROM clusters, cte WHERE cte.parent_id = clusters.id
            )
            SELECT
                cte.*,
                di.display_name issue_display_name,
                it.name issue_type_name,
                it.severity issue_severity
            FROM
                cte
            JOIN dataset_issues di ON cte.id = di.cluster_id
            JOIN issue_type it ON di.type_id = it.id
            WHERE
                parent_id is NULL
                AND cte.dataset_id = :dataset_id
            ;
            """
        query_result = await session.execute(
            sa.text(stmt),
            {"cluster_id": cluster_id, "dataset_id": dataset_id, "user_id": user_id}
        )
        row = query_result.mappings().one_or_none()
        return from_db_row(Cluster, row) if row else None

    @staticmethod
    @log_exception_with_args
    def _get_issues_by_cluster_ids(
            user_id: UUID,
            dataset_id: UUID,
            cluster_ids: List[UUID],
            session: Session,
    ) -> List[dict]:
        raise NotImplementedError()

    @staticmethod
    @log_exception_with_args
    async def _get_clusters_recursively(
            dataset_id: UUID,
            root_cluster_id: UUID,
            cluster_id: UUID,
            user_id: UUID,
            session: AsyncSession,
    ) -> List[Dict]:
        query_result = await session.execute(sa.text("""
            WITH RECURSIVE cte AS (
                SELECT clusters.*, 1 depth FROM clusters WHERE clusters.id = :cluster_id
                UNION ALL
                SELECT clusters.*, depth + 1 FROM clusters, cte WHERE clusters.parent_id = cte.id AND depth < 3
            )
            SELECT
                cte.*,
                dataset_issues.display_name issue_display_name,
                issue_type.name issue_type_name,
                issue_type.severity issue_severity
            FROM
                cte, datasets, dataset_issues, issue_type
            WHERE
                cte.dataset_id = datasets.id
                AND dataset_issues.cluster_id = :root_cluster_id
                AND issue_type.id = dataset_issues.type_id
                AND datasets.id = :dataset_id
                AND NOT datasets.deleted
            ;"""), {"cluster_id": cluster_id, "root_cluster_id": root_cluster_id, "dataset_id": dataset_id,
                    "user_id": user_id}
        )
        rows = query_result.mappings().all()
        return rows

    @staticmethod
    @log_exception_with_args
    def get_cluster_path(cluster_id: UUID, user_id: UUID) -> Optional[List[ClusterPath]]:
        stmt = """
            WITH RECURSIVE cte AS (
                SELECT * FROM clusters WHERE clusters.id = :cluster_id
                UNION ALL SELECT clusters.* FROM clusters, cte
                WHERE cte.parent_id = clusters.id
            )
            SELECT * FROM cte;
        """
        with get_session() as session:
            rows: List[Dict] = session.execute(sa.text(stmt), {"cluster_id": cluster_id}).mappings().all()

            breadcrumbs: List[ClusterPath] = []
            dataset_id: Optional[UUID] = None
            for row in rows:
                breadcrumb = ClusterPath.from_db_row(row)
                breadcrumbs.insert(0, breadcrumb)
                dataset_id = row['dataset_id']

            if dataset_id:
                dataset: Dataset = DatasetDB.get_by_id(dataset_id, user_id)
                breadcrumbs.insert(0, ClusterPath(type='DATASET', id=dataset.dataset_id,
                                                  display_name=dataset.display_name))

            return breadcrumbs

    @staticmethod
    @log_exception_with_args
    async def get_cluster_of_images(dataset_id: UUID, cluster_id: UUID, user_id: UUID) -> Optional[ClusterOfImages]:
        async with get_async_session() as session:
            # this is to get cluster's issue properties - they are currently associated only with root cluster
            root_cluster: Cluster = await ClusterDB._get_root_cluster_by_child_cluster(
                dataset_id, cluster_id, user_id, session)
            if not root_cluster:
                raise Exception(f'Failed to get root cluster for dataset {dataset_id} and user {user_id}')

            cluster: ChildCluster = await ClusterDB._get_leaf_cluster(cluster_id, user_id, session)
            if not cluster:
                return None

            leaf_cluster: ClusterOfImages = ClusterOfImages(
                id=cluster.cluster_id,
                dataset_id=cluster.dataset_id,
                cluster_type=ClusterType.IMAGES,
                name=cluster.name,
                n_clusters=cluster.n_clusters,
                n_child_clusters=cluster.n_child_clusters,
                n_images=cluster.n_images,
                n_objects=cluster.n_objects,
                size_bytes=cluster.size_bytes,
                issue_display_name=root_cluster.issue_display_name,
                issue_severity=root_cluster.issue_severity,
                issue_type_id=root_cluster.issue_type_id,
                issue_type_name=root_cluster.issue_type_name
            )

            leaf_cluster.stats = ClusterStats(
                label_distribution=await LabelDal.get_cluster_label_distribution(
                    session, leaf_cluster)
            )

            images: List[ImageForLeafClusterView] = await ClusterDB._get_images_for_leaf_cluster_view(
                leaf_cluster.cluster_id, leaf_cluster.issue_type_id, session)
            leaf_cluster.images = images
            return leaf_cluster

    @staticmethod
    @log_exception_with_args
    async def _get_images_for_leaf_cluster_view(
            cluster_id: UUID,
            issue_type_id: int,
            session: AsyncSession,
    ) -> List[ImageForLeafClusterView]:
        stmt = """
            SELECT * FROM images 
            JOIN (
            SELECT ic.image_id as image_id_, l.type, COUNT(*) as cnt
            FROM images_to_clusters ic 
            LEFT JOIN labels l ON ic.image_id = l.image_id
            WHERE ic.cluster_id = :cluster_id
            GROUP BY image_id_, l.type
            ) tmp ON images.id = tmp.image_id_
            """
        images: Dict[UUID, ImageForLeafClusterView] = {}
        qr = await session.execute(sa.text(stmt), {"cluster_id": cluster_id})
        rows = qr.mappings().all()
        for row in rows:
            _id: UUID = row['id']
            if _id in images:
                image = images[_id]
            else:
                image = ImageForLeafClusterView(
                    id=row['id'],
                    dataset_id=row['dataset_id'],
                    image_uri=row['image_uri'],
                    original_uri=row['original_uri'],
                    width=row['w'],
                    height=row['h'],
                    file_size=row['file_size'],
                    mime_type=row['mime_type']
                )
                images[_id] = image

            if row['type'] == LabelType.IMAGE.name:
                image.n_image_labels += row['cnt']
            elif row['type'] == LabelType.OBJECT.name:
                image.n_object_labels += row['cnt']

        stmt1 = """
            SELECT i.id, count(*) AS cnt 
            FROM images i 
            JOIN image_issues l ON i.id = l.image_id 
            JOIN images_to_clusters ic ON i.id = ic.image_id 
            WHERE ic.cluster_id = :cluster_id
            GROUP BY i.id;
            """

        qr = await session.execute(sa.text(stmt1), {"cluster_id": cluster_id})
        rows = qr.mappings().all()

        for row in rows:
            image_ = images.get(row['id'], None)
            if image_:
                image_.n_issues += row['cnt']

        qr = await session.execute(sa.text(
            """
            SELECT
                image_issues.image_id,
                image_issues.confidence 
            FROM
                image_issues, images_to_clusters
            WHERE
                image_issues.image_id = images_to_clusters.image_id 
                AND images_to_clusters.cluster_id = :cluster_id
                AND image_issues.type_id = :issue_type_id
            """),
            {"cluster_id": cluster_id, "issue_type_id": issue_type_id}
        )
        rows = qr.mappings().all()
        for row in rows:
            image_ = images.get(row['image_id'], None)
            if image_:
                image_.issue_confidence = row['confidence']

        return list(images.values())

    @staticmethod
    @log_exception_with_args
    async def get_cluster_of_objects(dataset_id: UUID, cluster_id: UUID, user_id: UUID) -> Optional[ClusterOfObjects]:
        async with get_async_session() as session:
            root_cluster: Cluster = await ClusterDB._get_root_cluster_by_child_cluster(
                dataset_id, cluster_id, user_id, session)
            if not root_cluster:
                raise Exception(f'Failed to get root cluster for dataset {dataset_id} and user {user_id}')

            cluster: ChildCluster = await ClusterDB._get_leaf_cluster(cluster_id, user_id, session)
            if not cluster:
                return None

            leaf_cluster: ClusterOfObjects = ClusterOfObjects(
                id=cluster.cluster_id,
                dataset_id=cluster.dataset_id,
                cluster_type=ClusterType.IMAGES,
                name=cluster.name,
                n_clusters=cluster.n_clusters,
                n_child_clusters=cluster.n_child_clusters,
                n_images=cluster.n_images,
                n_objects=cluster.n_objects,
                size_bytes=cluster.size_bytes,
                issue_display_name=root_cluster.issue_display_name,
                issue_severity=root_cluster.issue_severity,
                issue_type_id=root_cluster.issue_type_id,
                issue_type_name=root_cluster.issue_type_name
            )

            leaf_cluster.stats = ClusterStats(
                label_distribution=await LabelDal.get_cluster_label_distribution(
                    session, leaf_cluster)
            )

            images: List[ImageWithObject] = await ClusterDB._get_objects_for_leaf_cluster_view(
                user_id, leaf_cluster.cluster_id, leaf_cluster.issue_type_id, session)
            leaf_cluster.images = images
            return leaf_cluster

    @staticmethod
    @log_exception_with_args
    async def _get_objects_for_leaf_cluster_view(
            user_id: UUID,
            cluster_id: UUID,
            issue_type_id: int,
            session: AsyncSession,
    ) -> List[ImageWithObject]:
        res: List[ImageWithObject] = []
        qr = await session.execute(sa.text(
            """
                SELECT
                    images.id,
                    images.dataset_id,
                    images.image_uri,
                    images.original_uri,
                    images.w AS width,
                    images.h AS height,
                    images.file_size,
                    images.mime_type,
                    image_issues.confidence issue_confidence,
                    objects.object_id,
                    labels.bounding_box,
                    labels.category_display_name AS class_name,
                    (select count(*) from image_issues where cause=objects.object_id) object_issue_count
                FROM objects, clusters, images, labels, image_issues
                WHERE
                    objects.cluster_id = :cluster_id
                    AND clusters.id = objects.cluster_id
                    AND objects.image_id = images.id
                    AND image_issues.image_id = images.id
                    AND image_issues.cause = objects.object_id
                    AND image_issues.type_id = clusters.issue_type_id
                    AND labels.id = objects.object_id;
            """),
            {"cluster_id": cluster_id, "user_id": user_id}
        )
        rows: List[Dict] = qr.mappings().all()

        for row in rows:
            res.append(ImageWithObject(**row))

        return res

    @staticmethod
    @log_exception_with_args
    async def _get_leaf_cluster(cluster_id: UUID, user_id: UUID, session: AsyncSession) -> Optional[ChildCluster]:
        stmt = """
            SELECT
                *
            FROM
                clusters
            WHERE
                clusters.id = :cluster_id;
        """
        query_result = await session.execute(sa.text(stmt), {"cluster_id": cluster_id, "user_id": user_id})
        row: Optional[Dict] = query_result.mappings().one_or_none()
        return from_db_row(ChildCluster, row) if row else None

    @staticmethod
    @log_exception_with_args
    async def get_cluster(
            dataset_id: UUID,
            cluster_id: UUID,
            user_id: UUID,
            max_previews: int = 0,
    ) -> Optional[Cluster]:
        async with get_async_session() as session:

            root_cluster: Cluster = await ClusterDB._get_root_cluster_by_child_cluster(
                dataset_id, cluster_id, user_id, session)

            rows: List[dict] = await ClusterDB._get_clusters_recursively(
                dataset_id, root_cluster.cluster_id, cluster_id, user_id, session)

            if len(rows) == 0:
                return None

            # top cluster
            cluster: Cluster = from_db_row(Cluster, rows[0])
            cluster.stats = ClusterStats(
                label_distribution=await LabelDal.get_cluster_label_distribution(session, cluster)
            )

            # create sub clusters of the top cluster
            for row in rows:
                if row['depth'] == 2:
                    sub_cluster: ChildCluster = from_db_row(ChildCluster, row)
                    cluster.clusters.append(sub_cluster)

            sub_cluster_ids: List[UUID] = [c.cluster_id for c in cluster.clusters]

            previews: Dict[UUID, List[str]] = await get_previews(
                user_id=user_id,
                dataset_id=dataset_id,
                cluster_ids=sub_cluster_ids,
                max_num=max_previews,
                session=session
            )

            for sub_cluster in cluster.clusters:
                sub_cluster.previews = previews.get(sub_cluster.cluster_id)

            return cluster

    @staticmethod
    @log_exception_with_args
    def insert_cluster(
            session: Session,
            cluster_id: Optional[UUID],
            dataset_id: UUID,
            parent_id: Optional[UUID],
            cluster_type: ClusterType,
            issue_type_id: int,
            name: str,
            preview_uri: str,
            n_images: int = -1,
            n_clusters: int = -1,
            n_child_clusters: int = -1,
            n_objects: int = -1,
            size_bytes: int = -1,
            n_videos: int = -1,
            n_video_frames: int = -1
    ) -> UUID:
        if not cluster_id:
            cluster_id = uuid.uuid1()

        res_cluster_id: UUID = session.execute(sa.text(  # type: ignore
            """
            INSERT INTO
                clusters (
                    id, dataset_id, display_name, parent_id, type, issue_type_id,
                    preview_uri, n_images, n_objects, n_clusters, n_child_clusters, size_bytes, n_videos, 
                    n_video_frames)
            VALUES
                (:cluster_id, :dataset_id, :name, :parent_id, :cluster_type, :issue_type_id, :preview_uri,
                 :n_images, :n_objects, :n_clusters, :n_child_clusters, :size_bytes, :n_videos, :n_video_frames)
            RETURNING
                id;
            """),
            {
                "cluster_id": cluster_id,
                "dataset_id": dataset_id,
                "name": name,
                "parent_id": parent_id,
                "cluster_type": cluster_type.name,
                "issue_type_id": issue_type_id,
                "preview_uri": preview_uri,
                "n_images": n_images,
                "n_objects": n_objects,
                "n_clusters": n_clusters,
                "n_child_clusters": n_child_clusters,
                "size_bytes": size_bytes,
                "n_videos": n_videos,
                "n_video_frames": n_video_frames
            }
        ).one()[0]

        return res_cluster_id
