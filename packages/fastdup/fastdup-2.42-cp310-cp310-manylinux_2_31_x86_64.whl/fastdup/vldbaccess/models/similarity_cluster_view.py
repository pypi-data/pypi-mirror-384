from typing import Optional, Sequence, Mapping
from uuid import UUID

from pydantic import BaseModel

from fastdup.vl.utils import formatting
from fastdup.vl.utils.useful_decorators import log_exception_with_args, timed
from fastdup.vldbaccess.helpers import similarity_cluster_helpers
from fastdup.vldbaccess.models.media import Media
from fastdup.vldbaccess.similarity_cluster_model import SimilarityClusterType, SimilarityThreshold




@timed
def enrich_with_labels(clusters: list['SimilarityClusterView'], cluster_labels_rows: list[dict]):
    cluster_map: dict[UUID, "SimilarityClusterView"] = {cluster.cluster_id: cluster for cluster in clusters}
    for row in cluster_labels_rows:
        cluster_id = row['cluster_id']

        cluster: Optional["SimilarityClusterView"] = cluster_map.get(cluster_id, None)
        if not cluster:
            continue

        label_arrs = row['labels']

        for label_arr in label_arrs:
            if not label_arr:
                continue
            for label in label_arr:
                if not label:
                    continue
                counter: int = cluster.labels.get(label, 0)
                cluster.labels[label] = counter + 1

        cluster.labels = dict(sorted(cluster.labels.items(), key=lambda item: item[1], reverse=True))


class SimilarityClusterView(BaseModel):
    cluster_id: UUID
    type: SimilarityClusterType
    # display_name: Optional[str] = None
    n_images: int
    n_objects: int
    n_videos: int
    n_frames: int
    size_display_value: Optional[str] = None
    similarity_threshold: SimilarityThreshold
    previews: list[Media] = []
    labels: dict[str, int] = {}
    relevance_score: Optional[float] = None
    relevance_score_type: Optional[str] = None
    formed_by: Optional[str] = None
    __hash__ = object.__hash__

    @staticmethod
    @log_exception_with_args
    def from_dict_row(row: Mapping) -> 'SimilarityClusterView':
        relevance_score_type, relevance_score = similarity_cluster_helpers.get_relevance_score_and_type(
            row, cluster=True
        )
        similarity_cluster: SimilarityClusterView = SimilarityClusterView(
            cluster_id=row['cluster_id'],
            type=SimilarityClusterType[row['cluster_type']],
            # display_name=row['display_name'],
            n_images=row.get('n_images_filtered') or row.get('n_images') or -1,
            n_objects=row.get('n_objects_filtered') or row.get('n_objects') or -1,
            n_videos=row.get('n_videos_filtered') or row.get('n_videos') or -1,
            n_frames=row.get('n_frames_filtered') or row.get('n_frames') or -1,
            size_display_value=formatting.sizeof_fmt(row.get('size_bytes', -1), precision=0, suffix='B'),
            similarity_threshold=SimilarityThreshold.from_str(row['similarity_threshold']),
            labels=dict(row.get('cluster_labels') or []),
            relevance_score=relevance_score,
            relevance_score_type=relevance_score_type,
            formed_by=row.get('formed_by'),
        )
        return similarity_cluster

    @classmethod
    @log_exception_with_args
    @timed
    def from_row_list(cls, rows: Sequence[Mapping]) -> list['SimilarityClusterView']:
        id_to_cluster: dict[UUID, "SimilarityClusterView"] = {}
        for row in rows:
            cluster: Optional["SimilarityClusterView"] = id_to_cluster.get(row['cluster_id'], None)
            if cluster is None:
                cluster = cls.from_dict_row(row)
                assert cluster is not None
                id_to_cluster[row['cluster_id']] = cluster
            if cluster.type == 'IMAGES':
                cluster.previews.append(Media.from_image_row_dict(row))
            elif cluster.type == 'OBJECTS':
                cluster.previews.append(Media.from_object_row_dict(row))
            else:
                raise ValueError(f'Unknown similarity cluster type: {cluster.type}')

        return list(id_to_cluster.values())
