from uuid import UUID

from pydantic import BaseModel

from fastdup.vldbaccess.similarity_cluster_model import SimilarityClusterType


class SearchResult(BaseModel):
    entity_id: UUID
    entity_type: SimilarityClusterType
    distance: float
