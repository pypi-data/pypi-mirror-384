import json
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, validator

from fastdup.vl.common import logging_init
from fastdup.vl.utils import formatting
from fastdup.vl.utils.useful_decorators import log_exception_with_args
from fastdup.vldbaccess.base import (
    DatasetSourceType, SampleDataset, DatasetStatus, SeverityCount
)
from fastdup.vldbaccess.similarity_cluster_model import SimilarityThreshold


logger = logging_init.get_vl_logger(__name__)


class DatasetCounters(BaseModel):
    n_images: int
    n_objects: int
    n_videos: int
    n_frames: int


class DatasetStats(BaseModel):
    severity: int
    n_images: int
    n_images_display_value: str
    severity_display_name: str
    percentage: int


class Dataset(BaseModel):
    dataset_id: UUID = Field(alias='id')
    created_by: UUID
    owned_by: str
    display_name: str
    description: str
    preview_uri: str
    source_type: DatasetSourceType
    source_uri: str
    created_at: Optional[datetime] = None
    filename: Optional[str] = None
    sample: Optional[SampleDataset] = None
    status: DatasetStatus
    fatal_error_msg: Optional[str] = None
    progress: int
    score: int
    stats: List[SeverityCount] = []
    n_images: int
    n_objects: int
    n_clusters: int
    n_videos: int = -1
    n_video_frames: int = -1
    size_bytes: Optional[int] = None
    deleted: bool
    pipeline_commit_id: Optional[str] = None
    # calculated fields
    size_display_value: Optional[str] = None
    similarity_data: Optional[bool] = False
    thresholds: Optional[List[SimilarityThreshold]] = None
    media_embeddings: bool = False
    media_embeddings_cosine_distance: bool = False

    @validator("size_display_value", always=True)
    def _size_display_value(cls, v, values, **kwargs):
        try:
            val: int = -1 if values['size_bytes'] is None else values['size_bytes']
            return formatting.sizeof_fmt(val, precision=0, suffix='B')
        except KeyError as e:
            logger.error(f"Missing key {e} in dataset")
            return -1

    @validator("thresholds", always=True, pre=True)
    def _thresholds(cls, v, values, **kwargs):
        if v is not None and isinstance(v, str):
            return [SimilarityThreshold(t) for t in v.strip("{}").split(",")]
        return v

    @validator("n_videos", "n_video_frames", always=True, pre=True)
    def _n_videos(cls, v, values, **kwargs) -> int:
        return v if v is not None else -1

    @staticmethod
    @log_exception_with_args
    def from_dict_row(row: dict, severity_distribution: Optional[List[SeverityCount]] = None,
                      similarity_data=False) -> 'Dataset':

        thresholds = row.get("thresholds")
        if isinstance(thresholds, str) and thresholds.startswith("["):
            thresholds = json.loads(thresholds)
        dataset: Dataset = Dataset(
            id=row['id'],
            created_by=row['created_by'],
            owned_by=row['owned_by'],
            display_name=row['display_name'],
            description=row['description'],
            preview_uri=row['preview_uri'],
            source_type=DatasetSourceType[row['source_type']],
            source_uri=row['source_uri'],
            created_at=row['created_at'],
            filename=row['filename'],
            sample=None if not row['sample'] else SampleDataset[row['sample']],
            status=DatasetStatus[row['status']],
            fatal_error_msg=row['fatal_error_msg'],
            progress=row['progress'],
            score=row['score'],
            n_images=row.get('n_images', -1),
            n_objects=row.get('n_objects', -1),
            n_clusters=row.get('n_clusters', -1),
            n_videos=row.get('n_videos', -1),
            n_video_frames=row.get('n_video_frames', -1),
            size_bytes=row.get('size_bytes', -1),
            deleted=row['deleted'],
            pipeline_commit_id=row['pipeline_commit_id'],
            thresholds=thresholds,
            media_embeddings=row.get('media_embeddings', False),
            media_embeddings_cosine_distance=row.get('media_embeddings_cosine_distance', False)
        )

        if dataset.n_video_frames > 0:
            dataset.n_images -= dataset.n_video_frames

        if severity_distribution:
            dataset.stats = severity_distribution

        if similarity_data:
            dataset.similarity_data = similarity_data
        return dataset
