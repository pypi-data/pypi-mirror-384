from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
from uuid import UUID

from fastdup.vldbaccess.image import Image, Label, LabelCategory, ImageIssue
from fastdup.pipeline.common import algo_defaults

# The directory structure is defined by this doc:
# https://coda.io/d/Data-Pipeline_dlPHToHbykJ/Algo-Pipeline-for-V0-Launch_sua9W#_luhLm
OUT_DIR: Path = Path('processing')
STEP_ISSUE_GENERATOR_DIR: Path = OUT_DIR / 'step_issue_generator'
STEP_TREE_DIR: Path = OUT_DIR / 'step_tree'
STEP_EXPLORATION_DIR: Path = OUT_DIR / algo_defaults.DEFAULT_EXPLORATION_DIR
STEP_FASTDUP_DIR: Path = OUT_DIR / algo_defaults.DEFAULT_FASTDUP_DIR
IMAGE_METADATA_FILE: Path = OUT_DIR / 'image.metadata.parquet'
OBJECT_METADATA_FILE: Path = OUT_DIR / 'object.metadata.parquet'


@dataclass
class SyncDbContext:
    input_dir: Path
    images_data_path: Path = field(init=False)
    objects_data_path: Path = field(init=False)
    images_file: Path = field(init=False)
    objects_file: Path = field(init=False)
    clusters_file: Path = field(init=False)
    images_similarity_clusters_path: Path = field(init=False)
    objects_similarity_clusters_path: Path = field(init=False)
    images_similarity_mappings_path: Path = field(init=False)
    objects_similarity_mappings_path: Path = field(init=False)
    objects_assigned_cluster_path: Path = field(init=False)
    image_metadata_path: Path = field(init=False)
    object_to_thumbnails_mapping: Path = field(init=False)
    dataset_id: UUID
    images: OrderedDict[UUID, Image] = field(default_factory=OrderedDict)
    label_categories: Dict[int, LabelCategory] = field(default_factory=dict)
    labels: List[Label] = field(default_factory=list)
    issues: List[ImageIssue] = field(default_factory=list)
    should_persist_entities: bool = True
    should_persist_issues: bool = True
    should_persist_similarities: bool = False
    should_persist_similarities_mapping: bool = False
    should_persist_similarities_dry_run: bool = False
    should_persist_embeddings: bool = True

    image_sizes: Dict[UUID, int] = field(default_factory=dict)
    video_sources: Dict[UUID, str] = field(default_factory=dict)

    def __post_init__(self):
        self.images_data_path = self.input_dir / STEP_FASTDUP_DIR / 'images' / 'metadata.parquet'
        self.objects_data_path = self.input_dir / STEP_FASTDUP_DIR / 'objects' / 'metadata.parquet'
        self.images_issues_path = self.input_dir / STEP_ISSUE_GENERATOR_DIR / 'images_issues.parquet'
        self.objects_issues_path = self.input_dir / STEP_ISSUE_GENERATOR_DIR / 'objects_issues.parquet'
        self.clusters_file = self.input_dir / STEP_TREE_DIR / 'origin.json'
        self.images_similarity_clusters_path = self.input_dir / STEP_EXPLORATION_DIR / 'images_similarity_clusters.parquet'
        self.objects_similarity_clusters_path = self.input_dir / STEP_EXPLORATION_DIR / 'objects_similarity_clusters.parquet'
        self.images_similarity_mappings_path = self.input_dir / STEP_EXPLORATION_DIR / 'images_neighbors.parquet'
        self.objects_similarity_mappings_path = self.input_dir / STEP_EXPLORATION_DIR / 'objects_neighbors.parquet'
        self.objects_assigned_cluster_path = self.input_dir / STEP_EXPLORATION_DIR / 'objects_assigned_cluster.parquet'
        self.image_metadata_path = (
                self.input_dir /
                OUT_DIR /
                algo_defaults.DEFAULT_STEP_METADATA_DIR /
                algo_defaults.IMAGES_METADATA_OUT_FILENAME
        )
        self.object_metadata_path = (
                self.input_dir /
                OUT_DIR /
                algo_defaults.DEFAULT_STEP_METADATA_DIR /
                algo_defaults.OBJECTS_METADATA_OUT_FILENAME
        )
        self.object_to_thumbnails_mapping = self.input_dir / STEP_FASTDUP_DIR / 'objects/object_thumbnails.parquet'

    @property
    def step_fastdup_dir(self) -> Path:
        return self.input_dir / STEP_FASTDUP_DIR
