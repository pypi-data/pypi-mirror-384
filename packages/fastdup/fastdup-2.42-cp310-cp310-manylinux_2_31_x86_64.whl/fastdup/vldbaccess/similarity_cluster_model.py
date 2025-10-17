from enum import Enum
from typing import List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, validator, Field

from fastdup.vldbaccess.cluster_model import ImageForLeafClusterView, ImageWithObject
from fastdup.vl.utils.useful_decorators import log_exception_with_args
from fastdup.vl.utils import formatting
from fastdup.vldbaccess.models.media import Media


class SimilarityThreshold(str, Enum):
    ZERO = '0'
    ONE = '1'
    TWO = '2'
    THREE = '3'
    FOUR = '4'

    def __str__(self):
        return self.value

    @classmethod
    def from_int(cls, threshold: int) -> 'SimilarityThreshold':
        return cls.from_str(str(threshold))

    @classmethod
    def from_str(cls, threshold: str) -> 'SimilarityThreshold':
        return cls(threshold)


class SimilarityClusterType(str, Enum):
    IMAGES = 'IMAGES'
    OBJECTS = 'OBJECTS'

    @staticmethod
    def names():
        return [e for e in SimilarityClusterType]

    def __repr__(self):
        return self.value


class SimilarityCluster(BaseModel):
    id: UUID
    dataset_id: UUID
    type: SimilarityClusterType
    display_name: Optional[str] = None
    n_images: int
    n_objects: int
    size_bytes: int
    size_display_value: Optional[str] = None
    similarity_threshold: SimilarityThreshold
    previews: List[Media] = Field(default_factory=list)
    formed_by: str = "SIMILARITY"
    __hash__ = object.__hash__

    @validator("size_display_value", always=True)
    def _size_display_value(cls, v, values, **kwargs):
        return formatting.sizeof_fmt(values['size_bytes'], precision=0, suffix='B')

    def to_tuple(self) -> Tuple:
        return (
            self.id, self.dataset_id, self.type.value, self.display_name, self.n_images, self.n_objects,
            self.size_bytes, self.similarity_threshold.value
        )

    @staticmethod
    @log_exception_with_args
    def from_dict_row(row: dict) -> 'SimilarityCluster':
        similarity_cluster: SimilarityCluster = SimilarityCluster(
            id=row['id'],
            dataset_id=row['dataset_id'],
            type=SimilarityClusterType[row['cluster_type']],
            display_name=row['display_name'],
            n_images=row.get('n_images', -1),
            n_objects=row.get('n_objects', -1),
            size_bytes=row.get('size_bytes', -1),
            similarity_threshold=SimilarityThreshold.from_str(row['similarity_threshold']),
            formed_by=row['formed_by']
        )
        return similarity_cluster


class SimilarityClusterOfImages(SimilarityCluster):
    preview_images: List[ImageForLeafClusterView] = []


class SimilarityClusterOfObjects(SimilarityCluster):
    preview_objects: List[ImageWithObject] = []
