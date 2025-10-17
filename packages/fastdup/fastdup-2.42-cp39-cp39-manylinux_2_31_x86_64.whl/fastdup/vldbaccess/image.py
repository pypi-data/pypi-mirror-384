import json
import os
import urllib.parse
from datetime import time, datetime, timedelta
from enum import Enum
from typing import List, Tuple, Optional, Mapping
from uuid import UUID

import sqlalchemy as sa
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from fastdup.vl.common import logging_helpers, utils
from fastdup.vl.common.settings import Settings
from fastdup.vl.utils import formatting
from fastdup.vl.utils.uri_utils import get_video_serving_uri
from fastdup.vl.utils.useful_decorators import log_exception_with_args, timed
from fastdup.vldbaccess.base import BaseDB, Severity
from fastdup.vldbaccess.connection_manager import get_session
from fastdup.vldbaccess.issue_type import IssueTypeDal, IssueType


class LabelType(str, Enum):
    IMAGE = "IMAGE"
    OBJECT = "OBJECT"

    def __str__(self):
        return self.value


class LabelSource(str, Enum):
    VL = "VL"
    USER = "USER"


class LabelCategory(BaseModel):
    id: UUID
    original_id: int
    display_name: str
    dataset_id: UUID


class Label(BaseModel):
    id: UUID
    dataset_id: UUID
    original_id: int
    image_id: UUID
    category_id: UUID
    category_display_name: str
    type: LabelType
    type_display_name: str
    bounding_box: Optional[List[int]] = None
    source: LabelSource

    @staticmethod
    @log_exception_with_args
    def from_db_row(row: dict):
        return Label(
            id=row['id'],
            dataset_id=row['dataset_id'],
            original_id=row['original_id'],
            image_id=row['image_id'],
            category_id=row['category_id'],
            category_display_name=row['category_display_name'],
            type=LabelType[row['type']],
            type_display_name=row['type'],
            bounding_box=row['bounding_box'],
            source=row['source']
        )


class ImageSimilarityMapping(BaseModel):
    image_id: UUID
    similar_image_id: UUID
    distance: float

    @staticmethod
    @log_exception_with_args
    def from_db_row(row: dict):
        return ImageSimilarityMapping(
            image_id=row['image_id'],
            similar_image_id=row['similar_image_id'],
            distance=row['distance']
        )


class ImageSimilarityClusterLink(BaseModel):
    cluster_id: UUID
    image_id: UUID
    dataset_id: UUID
    order_in_cluster: int
    preview_order: int

    @staticmethod
    @log_exception_with_args
    def from_db_row(row: dict):
        return ImageSimilarityClusterLink(
            cluster_id=row['cluster_id'],
            image_id=row['image_id'],
            dataset_id=row['dataset_id'],
            order_in_cluster=row['order_in_cluster'],
            preview_order=row['preview_order']
        )


class ImageIssue(BaseModel):
    id: UUID
    type_id: int
    type_display_name: str
    image_id: UUID
    dataset_id: UUID
    description: Optional[str] = None
    cause: Optional[UUID] = None
    confidence: float
    severity: Severity
    # calculated field
    severity_display_name: Optional[str] = None

    @classmethod
    @validator("severity_display_name", always=True)
    def _severity_display_name(cls, v, values, **_kwargs):
        return values['severity'].display_name()

    @staticmethod
    @log_exception_with_args
    def from_db_row(row: dict, issue_types: List[IssueType]):
        issue_type_id = row['type_id']

        issue_type = next(filter(lambda x: x.id == issue_type_id, issue_types), None)
        if not issue_type:
            raise ValueError(f'Failed to resolve image issue type by id {issue_type_id}')

        return ImageIssue(
            id=row['id'],
            type_id=issue_type_id,
            type_display_name=issue_type.name,
            image_id=row['image_id'],
            dataset_id=row['dataset_id'],
            description=row['description'],
            cause=row['cause'],
            confidence=row['confidence'],
            severity=Severity(row['severity']),
        )


class Image(BaseModel):
    id: UUID
    dataset_id: UUID
    image_uri: str
    original_uri: str
    width: int
    height: int
    file_size: int
    mime_type: str
    issue_confidence: float = -1
    video_uri: Optional[str] = None
    frame_timestamp: Optional[time] = None
    video_duration: Optional[time] = None

    # calculated field
    file_size_display_value: Optional[str] = None
    file_name: str = ''
    video_name: Optional[str] = None

    @classmethod
    @validator("file_size_display_value", always=True)
    def _file_size_display_value(cls, v, values, **_kwargs):
        return formatting.sizeof_fmt(values['file_size'], precision=0, suffix='B')

    @classmethod
    @validator("file_name", always=True)
    def _file_name(cls, v, values, **_kwargs) -> str:
        original_uri: str = values['original_uri']
        return original_uri.rsplit('/', 1)[-1]

    @classmethod
    @validator("frame_timestamp", "video_duration", pre=True)
    def _frame_timestamp(cls, v, values, **_kwargs) -> Optional[time]:
        if v and isinstance(v, float):
            return (datetime.min + timedelta(seconds=v)).time()
        if v and isinstance(v, str):
            return time.fromisoformat(v)

        return v

    @staticmethod
    def _video_name(metadata: dict) -> Optional[str]:
        if metadata and 'video' in metadata and metadata['video']:
            return metadata['video'].rsplit('/', 1)[-1]

        return None

    @staticmethod
    @log_exception_with_args
    def from_db_row(row: dict):
        metadata = row['metadata'] or {}

        # duckdb returns metadata as string, not dict
        if metadata and isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}
        return Image(
            id=row['id'],
            dataset_id=row['dataset_id'],
            image_uri=row['image_uri'],
            original_uri=row['original_uri'],
            width=row['w'],
            height=row['h'],
            file_size=row['file_size'],
            mime_type=row['mime_type'],
            video_uri=get_video_serving_uri(row['dataset_id'], metadata),
            video_name=Image._video_name(metadata),
            frame_timestamp=metadata.get('frame_timestamp'),
            video_duration=metadata.get('video_duration'),
        )


class ImageDal(BaseDB):
    BATCH_SIZE = 1000

    @staticmethod
    @log_exception_with_args
    def save_images(images: List[Image]):
        statement = """
                    insert into images (id, dataset_id, image_uri, original_uri, w, h, file_size, mime_type) 
                    values (:id, :dataset_id, :image_uri, :original_uri, :width, :height, :file_size, :mime_type);
                    """

        with get_session(autocommit=True) as session:
            for batch in utils.iter_batches(images, batch_size=ImageDal.BATCH_SIZE, func=lambda x: x.dict()):
                session.execute(sa.text(statement), batch)

    @staticmethod
    @log_exception_with_args
    def link_images_to_clusters(dataset_id: UUID, cluster_id: UUID, image_id: UUID, session: Session):
        # TODO this is a mess, rewrite to follow ImageDal semantics
        statement = """
            INSERT INTO images_to_clusters (cluster_id, image_id, dataset_id) 
            VALUES (:cluster_id, :image_id, :dataset_id)
            ON CONFLICT DO NOTHING;
            """
        session.execute(
            sa.text(statement),
            {"cluster_id": cluster_id, "image_id": image_id, "dataset_id": dataset_id}
        )

    @staticmethod
    @log_exception_with_args
    @timed
    def link_images_to_similarity_clusters(links: List[ImageSimilarityClusterLink]):
        statement = """
            INSERT INTO images_to_similarity_clusters (cluster_id, image_id, dataset_id, order_in_cluster, 
            preview_order) 
            VALUES (:cluster_id, :image_id, :dataset_id, :order_in_cluster, :preview_order)
            ON CONFLICT DO NOTHING;
            """
        with get_session(autocommit=True) as session:
            for batch in utils.iter_batches(links, ImageDal.BATCH_SIZE, func=lambda x: x.dict()):
                session.execute(sa.text(statement), batch)

    @staticmethod
    @log_exception_with_args
    def save_label_categories(batch: List[LabelCategory]):
        """
        Under the assumption than even larger label categories corpuses count tens of K tops,
        and small property append_to of a category (basically - id and short text description), all can be persisted
        in a single batch insert.
        """
        statement = """
                    insert into label_categories (id, original_id, display_name, dataset_id) 
                    values (:id, :original_id, :display_name, :dataset_id);
                    """

        _batch = [label_category.dict() for label_category in batch]
        if len(_batch):
            with get_session(autocommit=True) as session:
                session.execute(sa.text(statement), _batch)

    @staticmethod
    @log_exception_with_args
    def save_labels(labels: List[Label]):
        statement = """
            insert into labels (id, dataset_id, original_id, image_id, category_id, category_display_name,
                                type, bounding_box, source) 
            values (:id, :dataset_id, :original_id, :image_id, :category_id,
                     :category_display_name, :type, :bounding_box, :source);
        """
        with get_session(autocommit=True) as session:
            for batch in utils.iter_batches(labels, ImageDal.BATCH_SIZE, func=lambda x: x.dict()):
                session.execute(sa.text(statement), batch)

    @staticmethod
    @log_exception_with_args
    def save_issues(dataset_id: UUID, issues: List[ImageIssue]):
        statement = """
                    insert into image_issues (id, type_id, image_id, dataset_id, description, cause, confidence) 
                    values (:id, :type_id, :image_id, :dataset_id, :description, :cause, :confidence);
                    """

        with get_session(autocommit=True) as session:
            for batch in utils.iter_batches(issues, batch_size=ImageDal.BATCH_SIZE, func=lambda x: x.dict()):
                session.execute(sa.text(statement), batch)

    @staticmethod
    def _get_image_raw(image_id: UUID, session: Session) -> Optional[Mapping]:
        row = session.execute(
            sa.text("SELECT * FROM images WHERE id = :image_id;"),
            {"image_id": image_id}
        ).mappings().one_or_none()
        return row

    @classmethod
    @log_exception_with_args
    def get_image(cls, image_id: UUID) -> Optional[Image]:
        with get_session() as session:
            row = cls._get_image_raw(image_id, session)

        if not row:
            return None

        return Image.from_db_row(row)

    @staticmethod
    def get_images_by_filename(image_filename: str, dataset_id: UUID, user_id: UUID) -> list[Image]:
        with get_session() as session:
            rows: List[dict] = session.execute(
                """
                SELECT
                    *
                FROM
                    images
                WHERE
                    split_part(original_uri, '/', -1) = :image_filename
                    AND dataset_id = :dataset_id
                """,
                {
                    'image_filename': image_filename,
                    'dataset_id': dataset_id,
                    'user_id': user_id,
                }
            ).mappings().all()

        return [Image.from_db_row(row) for row in rows]

    @staticmethod
    @log_exception_with_args
    def get_labels(image_id: UUID) -> List[Label]:
        with get_session() as session:
            rows: List[dict] = session.execute(sa.text("""
                SELECT
                    *
                FROM
                    labels
                WHERE
                    image_id = :image_id;
            """), {"image_id": image_id}).mappings().all()
        return [Label.from_db_row(row) for row in rows]

    @staticmethod
    @log_exception_with_args
    def get_issues(image_id: UUID) -> List[ImageIssue]:
        issue_types: List[IssueType] = IssueTypeDal.get_issue_types()
        with get_session() as session:
            rows: List[dict] = session.execute(sa.text("""
                SELECT
                    image_issues.*, issue_type.severity
                FROM
                    image_issues, issue_type
                WHERE
                    issue_type.id = image_issues.type_id
                    and image_issues.image_id = :image_id;
            """), {"image_id": image_id}).mappings().all()
        return [ImageIssue.from_db_row(row, issue_types) for row in rows]

    @staticmethod
    @log_exception_with_args
    def get_dataset_origins(dataset_id: UUID, user_id: UUID) -> list[str]:
        with get_session() as session:
            rows: list[Tuple] = session.execute(sa.text(
                """
                SELECT DISTINCT 
                    coalesce(metadata->>'origin', 'N/A') AS origin
                FROM
                    images
                WHERE
                    dataset_id = :dataset_id
                """),
                {
                    'user_id': user_id,
                    'dataset_id': dataset_id,
                }
            ).all()

        return [row[0] for row in rows]
