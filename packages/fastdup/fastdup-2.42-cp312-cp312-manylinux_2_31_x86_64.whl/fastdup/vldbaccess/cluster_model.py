from enum import Enum
from typing import List, Optional, Dict, Union, Type
from uuid import UUID

from pydantic import BaseModel, Field, validator

from fastdup.vl.utils import formatting
from fastdup.vl.utils.useful_decorators import log_exception_with_args
from fastdup.vldbaccess.base import Severity
from fastdup.vldbaccess.image import Image


class ClusterType(str, Enum):
    CLUSTERS = 'CLUSTERS'
    IMAGES = 'IMAGES'
    OBJECTS = 'OBJECTS'

    @staticmethod
    @log_exception_with_args
    def from_json_type(value: str) -> 'ClusterType':
        if value == 'images':
            return ClusterType.IMAGES
        elif value == 'objects':
            return ClusterType.OBJECTS
        elif value == 'clusters':
            return ClusterType.CLUSTERS
        else:
            raise ValueError(f'Unknown cluster type: {value}')


class ClusterStats(BaseModel):
    label_distribution: Dict[str, List[dict]]


# class PreviewBox(BaseModel):
#     image_uri: str
#     box: List[int]


class ClusterInfo(BaseModel):
    """
    The minimal information about a cluster.
    """
    cluster_id: UUID = Field(alias='id')
    dataset_id: UUID
    cluster_type: ClusterType
    name: str
    parent_id: Optional[UUID] = None


class PreviewLeafClusterView(ClusterInfo):
    """
    source_cluster_id is the id of a predecessor cluster for which this cluster is a preview supplier
    """
    source_cluster_id: UUID

    @staticmethod
    @log_exception_with_args
    def from_db_row(row: dict):
        return PreviewLeafClusterView(
            id=row['id'],
            dataset_id=row['dataset_id'],
            cluster_type=ClusterType[row['type']],
            name=row['display_name'],
            parent_id=row['parent_id'],
            source_cluster_id=row['source_cluster_id'],
        )


class ClusterBase(ClusterInfo):
    n_images: int
    n_objects: int
    n_clusters: int
    n_child_clusters: int
    size_bytes: int
    # calculated field
    size_display_value: Optional[str] = None
    affected_images_percentage: int = -1

    @validator("size_display_value", always=True)
    def _size_display_value(cls, v, values, **kwargs):
        return formatting.sizeof_fmt(values['size_bytes'], precision=0, suffix='B')


class ChildCluster(ClusterBase):
    previews: Optional[List[str]] = None
    preview_boxes: Optional[str] = None


class Cluster(ClusterBase):
    issue_display_name: str
    issue_type_id: int
    issue_type_name: str
    issue_severity: Severity
    issue_severity_display_name: Optional[str] = None     # calculated field
    confidence_score: float = 0.95
    largest_cluster_n_images: int = 450
    clusters: List[ChildCluster] = []
    stats: Optional[ClusterStats] = None

    @validator("issue_severity_display_name", always=True)
    def _severity_display_name(cls, v, values, **kwargs) -> str:
        severity: Severity = values['issue_severity']
        return severity.display_name()


class ImageForLeafClusterView(Image):
    n_issues: int = 0
    n_image_labels: int = 0
    n_object_labels: int = 0


class ImageWithObject(Image):
    object_id: UUID
    class_name: str
    bounding_box: List[int]
    object_issue_count: int


class LeafCluster(ClusterBase):
    issue_display_name: str
    issue_type_id: int
    issue_type_name: str
    issue_severity: Severity
    issue_severity_display_name: Optional[str] = None
    stats: Optional[ClusterStats] = None

    @validator("issue_severity_display_name", always=True)
    def _severity_display_name(cls, v, values, **kwargs) -> str:
        return values['issue_severity'].display_name()


class ClusterOfImages(LeafCluster):
    images: List[ImageForLeafClusterView] = []


class ClusterOfObjects(LeafCluster):
    images: List[ImageWithObject] = []


@log_exception_with_args
def from_db_row(clazz: Union[Type[Cluster], Type[ChildCluster]], row: dict) -> Union[Cluster, ChildCluster]:
    cluster_type: ClusterType = ClusterType[row['type']]
    n_clusters = row['n_clusters']
    n_child_clusters = row['n_child_clusters']
    n_images = row['n_images']
    n_objects = row['n_objects']
    if clazz == Cluster:
        return Cluster(
            id=row['id'],
            dataset_id=row['dataset_id'],
            name=row['display_name'],
            cluster_type=cluster_type,
            issue_display_name=row['issue_display_name'],
            issue_type_id=row['issue_type_id'],
            issue_type_name=row['issue_type_name'],
            issue_severity=Severity(row['issue_severity']),
            n_clusters=n_clusters,
            n_child_clusters=n_child_clusters,
            n_images=n_images,
            n_objects=n_objects,
            size_bytes=row['size_bytes'],
            clusters=[],
        )
    elif clazz == ChildCluster:
        return ChildCluster(
            id=row['id'],
            dataset_id=row['dataset_id'],
            name=row['display_name'],
            cluster_type=cluster_type,
            n_clusters=n_clusters,
            n_child_clusters=n_child_clusters,
            n_images=n_images,
            n_objects=n_objects,
            size_bytes=row['size_bytes'],
        )
    else:
        raise Exception(f"unexpected class {clazz}")
