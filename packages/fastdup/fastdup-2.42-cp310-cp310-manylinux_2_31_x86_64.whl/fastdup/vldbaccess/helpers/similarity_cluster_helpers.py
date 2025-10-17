from typing import Mapping, Optional, Tuple, Union

EPS = 0.1
RELEVANCE_SCORE_TYPES = [
    "cosine_similarity",
    "cosine_distance",
    "textual_search_relevance",
]
RELEVANCE_SCORE_TYPES_CLUSTERS = [*RELEVANCE_SCORE_TYPES, "n_media_filtered"]
RELEVANCE_SCORE_TYPES_PREVIEWS = [*RELEVANCE_SCORE_TYPES, "preview_order"]


def get_relevance_score_and_type(row: Mapping, cluster=False) -> Tuple[Optional[str], Optional[float]]:
    relevance_score_types = RELEVANCE_SCORE_TYPES_CLUSTERS if cluster else RELEVANCE_SCORE_TYPES_PREVIEWS
    for relevance_score_type in relevance_score_types:
        if relevance_score_type in row:
            return relevance_score_type, row[relevance_score_type]
    return None, None
