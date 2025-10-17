import ast

from typing import Optional
from uuid import UUID

from pydantic.v1 import BaseModel, validator, root_validator

from fastdup.vldbaccess.models.anchor_type import AnchorType
from fastdup.vldbaccess.models.dataset import Dataset
from fastdup.vldbaccess.similarity_cluster_model import SimilarityThreshold, SimilarityClusterType
from fastdup.vldbaccess.user import User


class ExplorationContext(BaseModel):
    user: Optional[User] = None
    user_id: UUID
    dataset: Optional[Dataset] = None
    dataset_id: UUID
    cluster_id: Optional[UUID] = None
    label_filter: Optional[list[str]] = None
    issue_type_filter: Optional[list[int]] = None
    caption_filter: Optional[str] = None
    date_from_filter: Optional[float] = None
    date_to_filter: Optional[float] = None
    origin_filter: Optional[list[str]] = None
    path_filter: str = ""
    entity_type: Optional[SimilarityClusterType] = None
    entity_type_filter: Optional[list[SimilarityClusterType]] = None
    threshold: Optional[SimilarityThreshold] = None
    tags: Optional[list[UUID]] = None
    untagged: Optional[bool] = None
    page_number: Optional[int] = None
    select_dataset_id_from: Optional[str] = None
    anchor_media_id: Optional[UUID] = None
    anchor_type: AnchorType = AnchorType.MEDIA
    media_embeddings: bool = False
    media_embeddings_cosine_distance: bool = False

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        if self.entity_type_filter and len(self.entity_type_filter) == 1:
            self.entity_type = self.entity_type_filter[0]
        if self.dataset and self.media_embeddings is None:
            self.media_embeddings = self.dataset.media_embeddings
        if self.dataset and self.media_embeddings_cosine_distance:
            self.media_embeddings_cosine_distance = self.dataset.media_embeddings_cosine_distance

    @validator("tags", "label_filter", "issue_type_filter", "entity_type_filter", "origin_filter", pre=True,
               allow_reuse=True)
    def _to_list(cls, value, values, config, field):
        if isinstance(value, str):
            return [field.type_(v.strip().strip('"\'')) for v in value.strip('[]').split(",")]
        return value

    @validator("path_filter", pre=True)
    def _normalize_path_filter(cls, path_filter: Optional[str]) -> str:
        if path_filter is None or len(path_filter) == 0 or path_filter == '/':
            return ""
        return path_filter.lstrip('/') + '%'

    @root_validator(pre=True)
    def _post_validate(cls, values):
        """
        1. if 'untagged' in the tags list, remove it and turn on untagged flag
        """
        if values.get('tags'):
            raw_tags = values.get('tags')
            if isinstance(raw_tags, list):
                raw_tags = str([str(tag) for tag in raw_tags])
            tags_str_arr: list[str] = ast.literal_eval(raw_tags)
            if 'untagged' in tags_str_arr:
                values['untagged'] = True
                tags_str_arr.remove('untagged')
                values['tags'] = None if len(tags_str_arr) == 0 else str(tags_str_arr)

        return values
