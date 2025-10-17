from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy import RowMapping
from sqlalchemy.orm import Session

from fastdup.vl.utils.useful_decorators import log_exception_with_args
from fastdup.vldbaccess.base import BaseDB
from fastdup.vldbaccess.connection_manager import get_session


class ObjectSimilarityMapping(BaseModel):
    image_id: UUID
    similar_image_id: UUID
    distance: float

    @staticmethod
    @log_exception_with_args
    def from_db_row(row: dict):
        return ObjectSimilarityMapping(
            image_id=row['image_id'],
            similar_image_id=row['similar_image_id'],
            distance=row['distance']
        )


class ObjectSimilarityClusterLink(BaseModel):
    cluster_id: UUID
    object_id: UUID
    dataset_id: UUID
    order_in_cluster: int
    preview_order: int

    @classmethod
    @log_exception_with_args
    def from_db_row(cls, row: dict):
        return cls(
            cluster_id=row['cluster_id'],
            object_id=row['object'],
            dataset_id=row['dataset_id'],
            order_in_cluster=row['order_in_cluster'],
            preview_order=row['preview_order']
        )


class Object(BaseModel):
    object_id: UUID
    image_id: UUID
    cluster_id: UUID
    dataset_id: UUID

    @classmethod
    @log_exception_with_args
    def from_db_row(cls, row: dict):
        return cls(
            object_id=row["object_id"],
            image_id=row["image_id"],
            cluster_id=row["cluster_id"],
            dataset_id=row["dataset_id"],
        )


class ObjectDAL(BaseDB):

    BATCH_SIZE = 1000

    @staticmethod
    @log_exception_with_args
    def insert_object(
            object_id: UUID,
            image_id: UUID,
            cluster_id: UUID,
            dataset_id: UUID,
            session: Session,
    ) -> None:
        session.execute(sa.text(
            """
            INSERT INTO objects (object_id, image_id, cluster_id, dataset_id)
            VALUES (:object_id, :image_id, :cluster_id, :dataset_id);
            """),
            {"object_id": object_id,  "image_id": image_id,
             "cluster_id": cluster_id, "dataset_id": dataset_id}
        )

    @staticmethod
    @log_exception_with_args
    def get_by_id(object_id: UUID, user_id: UUID) -> Optional[Object]:
        with get_session() as session:
            row: Optional[RowMapping] = session.execute(sa.text(
                """
                SELECT
                    object_id, image_id, cluster_id, dataset_id 
                FROM
                    objects
                WHERE
                    object_id = :object_id
                    LIMIT 1
                """),
                {"object_id": object_id, "user_id": user_id}
            ).mappings().one_or_none()
            if row is None:
                return None
            return Object.from_db_row(row)
