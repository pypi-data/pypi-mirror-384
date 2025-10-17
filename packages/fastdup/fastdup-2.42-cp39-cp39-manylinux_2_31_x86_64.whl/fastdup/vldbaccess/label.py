import sqlalchemy as sa

from typing import List, Dict, Optional, Sequence, Mapping
from uuid import UUID

from sqlalchemy import Row, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from fastdup.vl.utils.useful_decorators import timed, log_exception_with_args
from fastdup.vldbaccess.cluster_model import ClusterBase, ClusterType
from fastdup.vldbaccess.connection_manager import get_session, get_async_session
from fastdup.vldbaccess.image import LabelType


class LabelDal:
    @staticmethod
    @log_exception_with_args
    async def get_dataset_label_distribution(
            session: AsyncSession,
            dataset_id: UUID,
            n_images: int,
            n_objects: int,
    ) -> Dict[str, List[dict]]:
        stmt = """
            SELECT
                type, category_display_name, count(*) AS cnt
            FROM
                labels
            JOIN images ON labels.image_id = images.id
            -- images without issues are not associated with clusters, so we piggyback on that to filter them images out
            JOIN images_to_clusters itc on images.id = itc.image_id 
            WHERE
                images.dataset_id = :dataset_id
            GROUP BY
                type, category_display_name
            ORDER BY
                cnt
            DESC
            ;
        """
        rows: Sequence[Mapping] = (
            await session.execute(sa.text(stmt), {"dataset_id": dataset_id})
        ).mappings().all()
        return LabelDal.construct_distribution_from_db_rows(rows, n_images, n_objects)

    @staticmethod
    @log_exception_with_args
    def construct_distribution_from_db_rows(
            rows: List[dict],
            n_images: int,
            n_objects: int
    ) -> Dict[str, List[dict]]:
        distribution: Dict[str, List[dict]] = {}

        for row in rows:
            label_type = LabelType[row['type']]
            labels: List = distribution.get(label_type.name.lower(), [])
            total: int = n_images if label_type == LabelType.IMAGE else n_objects
            labels.append({
                'class': row['category_display_name'],
                'count': row['cnt'],
                'fraction': round(min(1, row['cnt'] / max(total, 1)), 3)
            })
            distribution[label_type.name.lower()] = labels
        return distribution

    @staticmethod
    @timed
    @log_exception_with_args
    async def get_cluster_label_distribution(session: AsyncSession, cluster: ClusterBase) -> Dict[str, List[dict]]:
        """
        It is definitely possible to fetch all the necessary data in one SQL, but I feel that the 1st statement
        is barely maintainable as it is, and adding a join with labels will render it unreadable.
        """

        image_id_rows: Sequence[Row] = (await session.execute(sa.text(
            """
                WITH RECURSIVE children_cls AS (
                    SELECT id, parent_id
                    FROM clusters
                    WHERE id = :cluster_id
                    UNION ALL
                    SELECT cls.id, cls.parent_id
                    FROM clusters cls
                    JOIN children_cls ON cls.parent_id = children_cls.id
                )
                SELECT DISTINCT images_to_clusters.image_id
                FROM children_cls
                JOIN images_to_clusters
                ON images_to_clusters.cluster_id = children_cls.id;
            """),
            {"cluster_id": cluster.cluster_id}
        )).all()
        image_ids: List[UUID] = [row[0] for row in image_id_rows]

        label_rows: Sequence[RowMapping] = (await session.execute(sa.text(
            """
                SELECT type, category_display_name, count(*) AS cnt
                FROM labels
                WHERE image_id = ANY (:image_ids)
                GROUP BY type, category_display_name
                ORDER BY cnt DESC;
            """), {"image_ids": image_ids}
        )).mappings().all()

        object_count: int = sum(row['cnt'] for row in label_rows if row['type'] == LabelType.OBJECT.name)

        return LabelDal.construct_distribution_from_db_rows(label_rows, len(image_ids), object_count)

    @staticmethod
    async def get_dataset_label_names(
            dateset_id: UUID,
            user_id: UUID,
            label_type_filter: Optional[list[LabelType]]
    ) -> list[str]:
        if label_type_filter is None or len(label_type_filter) != 1:
            query_filter = None
        elif label_type_filter[0] == LabelType.OBJECT:
            query_filter = ClusterType.OBJECTS
        else:
            query_filter = ClusterType.IMAGES

        query = """
            SELECT DISTINCT UNNEST(array_cat(labels, vl_labels))
            FROM
                flat_similarity_clusters
            WHERE dataset_id = :dataset_id
        """
        if query_filter is not None:
            query += f" AND cluster_type = :cluster_type"

        async with get_async_session() as session:
            qr = await session.execute(sa.text(query), {
                "dataset_id": dateset_id, "user_id": user_id, "cluster_type": query_filter
            })
            res = qr.all()
        return [row[0] for row in res]

    @staticmethod
    async def get_cluster_label_names(dateset_id: UUID, cluster_id: UUID, user_id: UUID) -> list[str]:
        async with get_async_session() as session:
            qr = await session.execute(sa.text("""
                SELECT DISTINCT unnest(array_cat(labels, vl_labels))
                FROM flat_similarity_clusters
                WHERE dataset_id = :dataset_id
                AND cluster_id = :cluster_id;                                
            """), {'dataset_id': dateset_id, 'user_id': user_id, 'cluster_id': cluster_id})
            res = qr.all()
        return [row[0] for row in res]
