from datetime import datetime
from enum import Enum
from typing import Union, Any, Optional, List, Annotated
from uuid import UUID

from pydantic import Field
from starlette.datastructures import URL

from fastdup.vl.common.pydantic_helper import OmitIfNone, Omit, AppResponseModel


class ExportTaskStatus(str, Enum):
    INIT = "INIT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MediaType(Enum):
    OBJECT = "object"
    IMAGE = "image"
    VIDEO = "video_frame"


class MetadataType(Enum):
    ISSUE = "issue"
    USER_TAG = "user_tag"
    VIDEO_INFO = "video_info"
    OBJECT_LABEL = "object_label"
    IMAGE_LABEL = "image_label"


class MetadataPropertiesLabels(AppResponseModel):
    original_id: int
    category_id: Annotated[Optional[UUID], Omit()] = None
    category_name: str
    source: str
    bbox: Annotated[Optional[List[int]], OmitIfNone()] = None


class MetadataPropertiesObjects(MetadataPropertiesLabels):
    url: Annotated[Optional[str], OmitIfNone()] = None
    metadata_items: List['MetadataExportInfo']


class MetadataPropertiesIssues(AppResponseModel):
    issue_type: str
    issues_description: Annotated[Optional[str], OmitIfNone()]
    confidence: float
    duplicate_group_id: Annotated[Optional[UUID], OmitIfNone()]


class MetadataExportInfo(AppResponseModel):
    id: Annotated[UUID, Omit()]
    type: MetadataType
    media_id: Annotated[UUID, Omit()]
    properties: Union[
        MetadataPropertiesObjects,
        MetadataPropertiesLabels,
        MetadataPropertiesIssues,
        dict[str, Any],
        None
    ]


class ImageExportInfo(AppResponseModel):
    media_id: UUID
    image_id: Annotated[UUID, Omit()]
    media_type: MediaType
    file_name: str
    file_path: str
    file_size: str
    height: int
    width: int
    url: str
    download_url: Annotated[str, Omit()]
    cluster_id: UUID
    metadata_items: List[MetadataExportInfo]



class GeneralExportInfo(AppResponseModel):
    schema_version: str = Field(default="1.1")
    dataset: str
    description: str
    dataset_url: str = ""
    export_task_id: Annotated[UUID, Omit()]
    export_time: datetime
    dataset_creation_time: datetime
    exported_by: str
    total_media_items: int

    class Config:
        arbitrary_types_allowed = True


class ExportInfo(AppResponseModel):
    info: GeneralExportInfo
    media_items: list[ImageExportInfo] = Field(default_factory=list)

    @property
    def export_name_suffix(self):
        return self.info.export_created

    @property
    def export_name(self):
        return f'vl_export_{self.export_name_suffix}'


class ExportTask(AppResponseModel):
    id: UUID
    dataset_id: UUID
    created_at: datetime
    download_uri: Optional[str]
    progress: float
    status: ExportTaskStatus


MetadataPropertiesObjects.update_forward_refs()