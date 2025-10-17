import json
from datetime import time
from enum import Enum
from typing import Optional, Mapping
from uuid import UUID

from pydantic import BaseModel

from fastdup.vl.utils.uri_utils import image_uri_to_thumb_uri, get_object_thumb_uri, get_video_serving_uri
from fastdup.vl.utils.common import concat_lists
from fastdup.vldbaccess.helpers import similarity_cluster_helpers


class MediaType(str, Enum):
    IMAGE = 'IMAGE'
    OBJECT = 'OBJECT'


class Media(BaseModel):
    type: MediaType
    media_id: UUID
    media_uri: str
    media_thumb_uri: str
    caption: Optional[str] = None
    image_id: Optional[UUID] = None
    image_uri: Optional[str] = None
    bounding_box: Optional[list[int]] = None
    file_name: Optional[str] = None
    original_uri: Optional[str] = None
    video_uri: Optional[str] = None
    frame_timestamp: Optional[time] = None
    labels: Optional[list[str]] = None
    relevance_score: Optional[float] = None
    relevance_score_type: Optional[str] = None

    def get_media_uri(self):
        return self.media_uri

    @staticmethod
    def from_image_row_dict(row: Mapping) -> 'Media':
        metadata: dict = row.get('metadata') or {}
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        relevance_score_type, relevance_score = similarity_cluster_helpers.get_relevance_score_and_type(row)

        media = Media(
            type=MediaType.IMAGE,
            media_id=row['image_or_object_id'],
            media_uri=row['image_uri'],
            media_thumb_uri=image_uri_to_thumb_uri(row['image_uri']),
            caption=row.get('caption', None),
            file_name=row['original_uri'].rsplit('/', 1)[-1] if row.get('original_uri') else '',
            original_uri=row['original_uri'],
            video_uri=get_video_serving_uri(row['dataset_id'], metadata, ''),
            frame_timestamp=metadata.get('frame_timestamp', None),
            labels=concat_lists(row['vl_labels'], row['labels']),
            relevance_score=relevance_score,
            relevance_score_type=relevance_score_type,
        )
        return media

    @staticmethod
    def from_object_row_dict(row: Mapping) -> 'Media':
        metadata = row.get('metadata') or {}
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        media: Media = Media(
            type=MediaType.OBJECT,
            media_id=row['image_or_object_id'],
            media_uri=row['image_uri'],
            media_thumb_uri=get_object_thumb_uri(row['dataset_id'], row['image_or_object_id'], row['dir_path']),
            image_id=row['image_id'],
            image_uri=row['image_uri'],
            bounding_box=None if row['bounding_box'] is None else row['bounding_box'],
            file_name=row['original_uri'].rsplit('/', 1)[-1] if row.get('original_uri') else '',
            original_uri=row['original_uri'],
            video_uri=get_video_serving_uri(row['dataset_id'], metadata, ''),
            frame_timestamp=metadata.get('frame_timestamp', None),
            labels=concat_lists(row['vl_labels'], row['labels'])
        )
        return media

    @staticmethod
    def from_row_dict(row: Mapping) -> 'Media':
        cluster_type = row['cluster_type']
        if cluster_type == 'IMAGES':
            return Media.from_image_row_dict(row)
        elif cluster_type == 'OBJECTS':
            return Media.from_object_row_dict(row)
        else:
            raise ValueError(f'Unknown similarity cluster type: {cluster_type}')
