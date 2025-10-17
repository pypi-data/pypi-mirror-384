from typing import Optional, List

from pydantic import BaseModel
from uuid import UUID

from fastdup.vldbaccess.models.exploration_context import ExplorationContext
from fastdup.vldbaccess.similarity_cluster_model import SimilarityClusterType
from fastdup.vldbaccess.user import User


class FiltersContext(BaseModel):
    labels: Optional[List[str]] = None
    issues: Optional[List[int]] = None
    origins: Optional[List[str]] = None
    caption: Optional[str] = None
    path: Optional[str] = None
    entity_type: Optional[List[SimilarityClusterType]] = None
    created_min_ms: Optional[float] = None
    created_max_ms: Optional[float] = None

    def parse_filters_to_exploration_context(
            self, user: User, dataset_id: UUID, cluster_id: Optional[UUID] = None) -> ExplorationContext:
        return ExplorationContext(
            label_filter=self.labels,
            issue_type_filter=self.issues,
            origin_filter=self.origins,
            date_from_filter=self.created_min_ms,
            date_to_filter=self.created_max_ms,
            entity_type_filter=self.entity_type,
            caption_filter=self.caption,
            path_filter=self.path,
            user=user,
            user_id=user.user_id,
            dataset_id=dataset_id,
            cluster_id=cluster_id
        )
