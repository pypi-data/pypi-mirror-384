import sqlalchemy as sa

from abc import ABC, abstractmethod
from typing import Dict, List, NamedTuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from fastdup.vl.utils.common import merge_dicts
from fastdup.vl.utils.uri_utils import image_uri_to_thumb_uri, get_object_thumb_uri
from fastdup.vl.utils.useful_decorators import log_exception_with_args
from fastdup.vldbaccess.cluster_model import ClusterType


class Previews(NamedTuple):
    image_previews: Dict[UUID, List[str]]
    object_previews: Dict[UUID, List[str]]


class PreviewsAbstractDAL(ABC):
    @staticmethod
    @abstractmethod
    async def image_previews(
            user_id: UUID,
            dataset_id: UUID,
            seed_cluster_ids: List[UUID],
            max_num: int,
            session: AsyncSession,
            include_object_previews: bool = False,
    ) -> Dict[UUID, List[str]]:
        pass

    @staticmethod
    @abstractmethod
    async def object_previews(
            user_id: UUID,
            dataset_id: UUID,
            seed_cluster_ids: List[UUID],
            max_num: int,
            session: AsyncSession,
    ) -> Dict[UUID, List[str]]:
        pass


class PreviewsByConfidenceDAL(PreviewsAbstractDAL):

    @staticmethod
    @log_exception_with_args
    async def image_previews(
            user_id: UUID,
            dataset_id: UUID,
            seed_cluster_ids: List[UUID],
            max_num: int,
            session: AsyncSession,
            include_object_previews: bool = False,
    ) -> Dict[UUID, List[str]]:

        cluster_type: List[str] = [ClusterType.IMAGES.value]
        if include_object_previews:
            cluster_type.append(ClusterType.OBJECTS.value)

        qr = await session.execute(sa.text(
            """
            WITH RECURSIVE cte AS (
                SELECT clusters.*, clusters.id seed FROM clusters WHERE clusters.id = ANY(:cluster_ids)
                UNION ALL
                SELECT clusters.*, cte.seed FROM clusters, cte WHERE clusters.parent_id = cte.id
            )
            SELECT image_uri, seed, rank FROM (
                SELECT
                    images.image_uri,
                    cte.seed,
                    rank() OVER (PARTITION BY seed ORDER BY confidence, original_uri DESC) AS rank
                FROM cte, images_to_clusters, images, image_issues
                WHERE
                    cte.type = ANY(:cluster_type)
                    AND cte.id = images_to_clusters.cluster_id
                    AND images_to_clusters.image_id = images.id
                    AND images.id = image_issues.image_id
                    AND image_issues.type_id = cte.issue_type_id
            ) ranked
            WHERE rank <= :max_num
            ORDER BY seed, rank;
            """),
            {'cluster_ids': seed_cluster_ids, 'cluster_type': cluster_type, 'user_id': user_id, 'max_num': max_num}
        )
        rows = qr.mappings().all()

        res: Dict[UUID, List[str]] = {}

        for row in rows:
            cluster_id: UUID = row['seed']
            if cluster_id not in res:
                res[cluster_id] = []
            res[cluster_id].append(row['image_uri'])

        return res

    @staticmethod
    @log_exception_with_args
    async def object_previews(
            user_id: UUID,
            dataset_id: UUID,
            seed_cluster_ids: List[UUID],
            max_num: int,
            session: AsyncSession,
    ) -> Dict[UUID, List[str]]:
        qr = await session.execute(sa.text(
            """
            WITH RECURSIVE cte AS (
                SELECT clusters.*, clusters.id seed FROM clusters WHERE clusters.id = ANY(:cluster_ids)
                UNION ALL
                SELECT clusters.*, cte.seed FROM clusters, cte WHERE clusters.parent_id = cte.id
            )
            SELECT image_uri, object_id, dir_path, seed, rank FROM (
                SELECT
                    images.image_uri,
                    objects_to_images.dir_path,
                    objects.object_id,
                    cte.seed,
                    rank() OVER (PARTITION BY seed ORDER BY confidence, original_uri DESC) AS rank
                FROM cte, images, image_issues, objects, objects_to_images
                WHERE
                    cte.type = 'OBJECTS'
                    AND objects_to_images.object_id = objects.object_id
                    AND cte.id = objects.cluster_id
                    AND objects.image_id = images.id
                    AND images.id = image_issues.image_id
                    AND image_issues.cause = objects.object_id
                    AND image_issues.type_id = cte.issue_type_id
            ) ranked
            WHERE rank <= :max_num
            ORDER BY seed, rank;
            """),
            {'cluster_ids': seed_cluster_ids, 'max_num': max_num, 'user_id': user_id}
        )
        rows = qr.mappings().all()

        res: Dict[UUID, List[str]] = {}
        row: dict

        for row in rows:
            cluster_id: UUID = row['seed']
            if cluster_id not in res:
                res[cluster_id] = []
            res[cluster_id].append(get_object_thumb_uri(dataset_id, row['object_id'], row['dir_path']))

        return res


class PreviewsByClusterSizeDAL(PreviewsAbstractDAL):

    @staticmethod
    # @log_exception_with_args
    async def image_previews(
            user_id: UUID,
            dataset_id: UUID,
            seed_cluster_ids: List[UUID],
            max_num: int,
            session: AsyncSession,
            include_object_previews: bool = False,
    ) -> Dict[UUID, List[str]]:

        qr = await session.execute(sa.text(
            """
            WITH RECURSIVE cte AS (
                SELECT clusters.*, clusters.id seed FROM clusters WHERE clusters.id = ANY(:cluster_ids)
                UNION ALL
                SELECT clusters.*, cte.seed FROM clusters, cte WHERE clusters.parent_id = cte.id
            )
            SELECT * FROM (
                SELECT
                    images.image_uri,
                    cte.seed,
                    cte.id leaf_cluster_id,
                    cte.n_images,
                    row_number() OVER (
                        PARTITION BY cte.seed
                        ORDER BY cte.n_images DESC, cte.id, images.file_size DESC, images.original_uri
                    ) rownum
                FROM images, images_to_clusters, cte
                WHERE
                    cte.type = 'IMAGES'
                    AND images_to_clusters.cluster_id = cte.id
                    AND images_to_clusters.image_id = images.id
            ) foo
            WHERE
                rownum <= :max_num
            ORDER BY
                seed, rownum
            """),
            {'cluster_ids': seed_cluster_ids, 'max_num': max_num, 'user_id': user_id}
        )
        rows = qr.mappings().all()
        res: Dict[UUID, List[str]] = {}

        for row in rows:
            cluster_id: UUID = row['seed']
            images_preview_uri: str = row['image_uri']
            res.setdefault(cluster_id, []).append(images_preview_uri)

        return res

    @staticmethod
    @log_exception_with_args
    async def object_previews(
            user_id: UUID,
            dataset_id: UUID,
            seed_cluster_ids: List[UUID],
            max_num: int,
            session: AsyncSession,
    ) -> Dict[UUID, List[str]]:
        qr = await session.execute(sa.text(
            """
            WITH RECURSIVE cte AS (
                SELECT clusters.*, clusters.id seed FROM clusters WHERE clusters.id = ANY(:cluster_ids)
                UNION ALL
                SELECT clusters.*, cte.seed FROM clusters, cte WHERE clusters.parent_id = cte.id
            )
            SELECT * FROM (
                SELECT
                    objects.object_id,
                    objects_to_images.dir_path,
                    images.image_uri,
                    cte.seed,
                    cte.id leaf_cluster_id,
                    labels.original_id,
                    cte.n_objects,
                    row_number() OVER (
                        PARTITION BY cte.seed
                        ORDER BY cte.n_objects DESC, cte.id, images.file_size DESC, labels.original_id
                    ) rownum
                FROM objects, objects_to_images, images, labels, image_issues, cte    
                WHERE
                    cte.type = 'OBJECTS'
                    AND objects.object_id = objects_to_images.object_id
                    AND objects.cluster_id = cte.id
                    AND objects.image_id = images.id
                    AND objects.object_id = labels.id
                    AND objects.object_id = image_issues.cause
                    AND image_issues.type_id = cte.issue_type_id
            ) foo
            WHERE
                rownum <= :max_num
            ORDER BY
                seed, rownum;
            """),
            {'cluster_ids': seed_cluster_ids, 'max_num': max_num, 'user_id': user_id}
        )
        rows = qr.mappings().all()

        res: Dict[UUID, List[str]] = {}

        for row in rows:
            cluster_id: UUID = row['seed']
            object_preview_uri: str = get_object_thumb_uri(dataset_id, row['image_uri'], row['dir_path'])
            res.setdefault(cluster_id, []).append(object_preview_uri)

        return res


@log_exception_with_args
async def get_previews(
        user_id: UUID,
        dataset_id: UUID,
        cluster_ids: List[UUID],
        max_num: int,
        session: AsyncSession,
) -> Dict[UUID, List[str]]:
    if max_num < 1:
        return {}

    # get the issue id for each cluster
    qr = await session.execute(
        sa.text("""
        SELECT id, issue_type_id
        FROM clusters
        WHERE
            id = ANY(:cluster_ids)
            AND dataset_id = :dataset_id 
        ;
        """),
        {'cluster_ids': cluster_ids, 'dataset_id': dataset_id, 'user_id': user_id}
    )
    cluster_id_issue_rows = qr.mappings().all()

    # split the cluster ids into separated lists by issue type
    clusters_of_duplicates: List[UUID] = []
    clusters_of_others: List[UUID] = []
    for row in cluster_id_issue_rows:
        if row['issue_type_id'] == 2:
            clusters_of_duplicates.append(row['id'])
        else:
            clusters_of_others.append(row['id'])

    # find previews for every group
    duplicate_image_previews: Dict[UUID, List[str]] = await PreviewsByClusterSizeDAL.image_previews(
        user_id, dataset_id, clusters_of_duplicates, max_num, session)
    duplicate_object_previews: Dict[UUID, List[str]] = await PreviewsByClusterSizeDAL.object_previews(
        user_id, dataset_id, clusters_of_duplicates, max_num, session)
    other_image_previews: Dict[UUID, List[str]] = await PreviewsByConfidenceDAL.image_previews(
        user_id, dataset_id, clusters_of_others, max_num, session)
    other_object_previews: Dict[UUID, List[str]] = await PreviewsByConfidenceDAL.object_previews(
        user_id, dataset_id, clusters_of_others, max_num, session)

    # update image previews to thumbnails
    image_previews: Dict[UUID, List[str]] = merge_dicts(duplicate_image_previews, other_image_previews)
    for _, img_preview_list in image_previews.items():
        for i in range(len(img_preview_list)):
            img_preview_list[i] = image_uri_to_thumb_uri(img_preview_list[i])

    # merge everything
    res: Dict[UUID, List[str]] = merge_dicts(image_previews, duplicate_object_previews, other_object_previews)
    return res
