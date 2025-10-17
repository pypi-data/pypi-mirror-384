from typing import Optional
from uuid import UUID

from pathlib import Path

from sqlalchemy import Engine

from fastdup.vldbaccess.image_embeddings.pg_store_image_embeddings import PGStoreImageEmbeddings
from fastdup.vldbaccess.image_embeddings.duckdb_store_image_embeddings import DuckDBStoreImageEmbeddings
from fastdup.vldbaccess.image_embeddings.abstract_image_embeddings import AbstractImageEmbeddings


def get_image_embeddings_service(
    engine: Engine,
    dataset_id: UUID,
    index_path: Optional[Path] = None
) -> AbstractImageEmbeddings:
    dialect = engine.dialect.name
    if dialect == "postgresql":
        return PGStoreImageEmbeddings(engine, dataset_id, index_path)
    elif dialect == "duckdb":
        return DuckDBStoreImageEmbeddings(engine, dataset_id, index_path)
    else:
        raise KeyError(f"Unsupported dialect {dialect}")
