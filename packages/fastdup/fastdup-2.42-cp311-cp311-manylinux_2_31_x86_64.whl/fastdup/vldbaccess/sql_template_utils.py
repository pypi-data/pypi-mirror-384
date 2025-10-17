import textwrap
from enum import Enum
from typing import NamedTuple

from fastdup.vl.common.const import APP_PATH
from fastdup.vl.common.settings import Settings
from fastdup.vldbaccess.connection_manager import get_engine_dialect


from jinja2 import Environment, FileSystemLoader

from fastdup.vldbaccess.models.anchor_type import AnchorType


class QueryModule(Enum):
    EXPLORATION = "EXPLORATION"
    DATASETS = "DATASETS"

    def __str__(self):
        return self.value.lower()


class TemplateContext(NamedTuple):
    dialect_name: str
    module: QueryModule


_template_environment_cache: dict[TemplateContext, Environment] = {}


def get_sql_templates_environment(module) -> Environment:
    dialect_name = get_engine_dialect()
    env = _template_environment_cache.setdefault(
        TemplateContext(dialect_name, module),
        _get_sql_templates_environment(module, dialect_name)
    )
    return env


def _get_sql_templates_environment(module: QueryModule, dialect_name: str) -> Environment:
    return Environment(
        loader=FileSystemLoader([
            APP_PATH.joinpath("vldbaccess", "raw_sql", dialect_name, str(module)),
            APP_PATH.joinpath("vldbaccess", "raw_sql", "base", str(module))
        ])
    )


def template_to_sql(query: str) -> str:
    with_no_empty_lines = "\n".join([s for s in query.splitlines() if s.strip().removesuffix('--')])
    return textwrap.dedent(with_no_empty_lines)


def query_context_by_module(module: QueryModule, kwargs) -> dict:
    if module == QueryModule.EXPLORATION:
        media_embeddings_cosine_distance = kwargs.get("media_embeddings_cosine_distance", False)
        filtered_query = any(
            bool(kwargs.get(filter_key)) for filter_key in [
                "label_filter", "issue_type_filter", "date_from_filter", "date_to_filter", "origin_filter",
                "path_filter", "tags"]
        )
        if filtered_query or (get_engine_dialect() == "duckdb"):
            search_similar_clusters_pre_filter_results = None
        else:
            search_similar_clusters_pre_filter_results = Settings.SEARCH_SIMILAR_CLUSTERS_PRE_FILTER_RESULTS

        return {
            "is_textual_search": (Settings.SORT_EXPLORATION_RESULTS_BY_TEXT_RELEVANCE
                                  and kwargs.get("caption_filter")),
            "similarity_using_vector_db": (
                (Settings.SEARCH_SIMILAR_CLUSTERS_USE_VECTOR_DB and kwargs.get("media_embeddings"))
                or (kwargs.get("media_embeddings") and kwargs.get("anchor_type", AnchorType.UPLOAD))
            ),
            "query_vector_table": kwargs.get("anchor_type", AnchorType.MEDIA).query_vector_table(),
            "similarity_metric": "<=>" if media_embeddings_cosine_distance else "<->",
            "cosine_similarity": (  # cosine similarity (duckdb) is desc vs cosine distance which is asc (pgvector)
                True if get_engine_dialect() == "duckdb" and media_embeddings_cosine_distance else False
            ),
            "search_similar_clusters_pre_filter_results": search_similar_clusters_pre_filter_results,
            "similarity_threshold": (None if get_engine_dialect() == "duckdb"
                                     else Settings.SEARCH_SIMILAR_SIMILARITY_THRESHOLD
                                     )
        }

    return {}


def render(module: QueryModule, query: str, **kwargs) -> str:
    query = template_to_sql(
        get_sql_templates_environment(module).get_template(query).render(
            Settings=Settings,
            **(query_context_by_module(module, kwargs) | kwargs)
        )
    )
    return query



