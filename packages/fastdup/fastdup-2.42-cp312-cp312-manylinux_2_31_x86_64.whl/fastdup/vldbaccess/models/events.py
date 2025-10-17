from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, root_validator, validator, Field

from fastdup.vl.common import logging_init
from fastdup.vldbaccess.models.limits import LimitType
from fastdup.vl.utils import formatting
from fastdup.vl.utils.annotation_utils import AnnotatedBoundingBox

logger = logging_init.get_vl_logger(__name__)


class Severity(str, Enum):
    OK = 'OK'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


class IngestedDataType(str, Enum):
    BUCKET = 'BUCKET'
    FOLDER = 'FOLDER'
    ZIP = 'ZIP'


class Event(BaseModel):
    serial: int = -1
    dataset_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = ''
    severity: Severity = Severity.OK

    @root_validator(pre=True)
    def set_event_type(cls, values):
        values['event_type'] = cls.__name__
        return values


class TransactionalEvent(Event):
    transaction_id: int


class InvalidInput(Event):
    reason: Optional[str] = None
    severity: Severity = Severity.WARNING


class ServerFailure(Event):
    error_reference_id: UUID
    reason: Optional[str] = None
    severity: Severity = Severity.ERROR


class DatasetInitialized(Event):
    dataset_id: UUID
    dataset_name: str


class DatasetInitializationFailed(ServerFailure):
    pass


class DataSourceEvent(TransactionalEvent):
    source_type: IngestedDataType


class S3Event(TransactionalEvent):
    s3_url: str


class FileEvent(TransactionalEvent):
    file_name: str


class S3InvalidURL(InvalidInput, S3Event):
    pass


class S3ValidURL(S3Event):
    pass


class S3NoAccess(InvalidInput, S3Event):
    pass


class S3Error(ServerFailure, S3Event):
    pass


class S3Connected(S3Event):
    pass


class S3FileDownloaded(FileEvent, S3Event):
    pass


class S3MediaPreview(FileEvent, S3Event):
    thumbnail: str
    scale_factor: float
    image_annotations: Optional[List[str]] = None
    object_annotations: Optional[List[AnnotatedBoundingBox]] = None


class S3NoPreview(InvalidInput, FileEvent, S3Event):
    pass


class FilesUploadStart(TransactionalEvent):
    pass


class MultipleFiles(TransactionalEvent):
    total_size_bytes: int
    total_size_display_value: Optional[str] = None
    total_files: int

    @validator("total_size_display_value", always=True)
    def _total_size_display_value(cls, v, values, **kwargs):
        try:
            val: int = -1 if values['total_size_bytes'] is None else values['total_size_bytes']
            return formatting.sizeof_fmt(val, precision=0, suffix='B')
        except KeyError as e:
            logger.error(f"Missing key {e}")
            return -1


class FilesChunkUploaded(MultipleFiles):
    folder_name: str


class FilesUploadCompleted(MultipleFiles):
    pass


class FileUploaded(FileEvent):
    pass


class FileMediaPreview(FileEvent):
    thumbnail: str
    scale_factor: float
    image_annotations: Optional[List[str]] = None
    object_annotations: Optional[List[AnnotatedBoundingBox]] = None


class FileNoPreview(FileEvent):
    pass


class PreviewReady(TransactionalEvent):
    pass


class AnnotationsValid(Event):
    file_names: List[str]


class AnnotationsInvalid(InvalidInput):
    pass


class AnnotationsCleared(Event):
    pass


class AnnotatedPreview(Event):
    pass


class DatasetStatus(Event):
    status: str
    progress: int


class FatalDatasetStatus(DatasetStatus, ServerFailure):
    severity: Severity = Severity.ERROR


class LimitExceeded(TransactionalEvent, InvalidInput):
    limit_type: LimitType
    limit_value: int
    actual_value: int


class LimitNotExceeded(TransactionalEvent):
    pass


class ArchiveUploaded(FileEvent):
    pass

