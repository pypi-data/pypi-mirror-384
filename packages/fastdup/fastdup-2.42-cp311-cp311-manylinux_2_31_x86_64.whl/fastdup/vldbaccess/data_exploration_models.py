from enum import auto, Flag, Enum
from typing import List, Dict, Optional

from pydantic import BaseModel


class MetadataSummarySection(Flag):
    USER_TAGS = auto()
    VIDEOS = auto()
    METADATA = auto()
    LABELS = auto()
    VL_LABELS = auto()
    ISSUES = auto()

    ALL = LABELS | VL_LABELS | USER_TAGS | VIDEOS | METADATA


class DisplaySection(Enum):
    USER_TAGS = "user_tags"
    ISSUES = "issues"
    VL_ENRICHMENT = "vl_enrichment"
    METADATA = "metadata"


class BaseExplorationSummary(BaseModel):
    # TODO: change to snakecase and render on response
    showVLEnrichment: bool
    totalElements: Optional[int] = None


class MetadataSummary(BaseExplorationSummary):
    # TODO: change to snakecase and render on response
    videoData: List[Dict]
    imageLabels: List[Dict]
    objectLabels: List[Dict]
    userTags: List[Dict]
    issueData: List[Dict]
    vlImageLabels: List[Dict]
    vlObjectLabels: List[Dict]
