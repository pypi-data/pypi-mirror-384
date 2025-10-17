import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

import pandas
import sqlalchemy as sa
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from fastdup.vl.common import logging_init
from fastdup.vl.utils.useful_decorators import timed
from fastdup.vldbaccess.image_embeddings.abstract_image_embeddings import AbstractImageEmbeddings, load_index, load_annotations

logger = logging_init.get_vl_logger(__name__)


class DuckDBStoreImageEmbeddings(AbstractImageEmbeddings):
    cosine_distance = True

    def __init__(self, engine: Engine, dataset_id: UUID, index_path: Optional[Path] = None):
        super().__init__(engine, dataset_id, index_path)
        self.records = 0

    def _store_data(self, path, id_column: str = "image_id", is_image=True):
        logger.info("Storing embeddings")
        numpy_index = load_index(path)
        annotations = load_annotations(path)

        with Session(self.engine) as session:
            ctx = [{
                "dataset_id": self.dataset_id,
                "media_id": UUID(image_id),
                "is_image": is_image,
                "embedding": embedding.tolist()
                } for (image_id, embedding) in zip(annotations[id_column], numpy_index)
            ]
            df = pandas.DataFrame(ctx)
            duckdb = session.connection().connection.connection
            duckdb.sql("INSERT INTO image_vector SELECT * FROM df")
            session.commit()
        self.records += len(numpy_index)

    @timed(context_keys=["self.dataset_id"])
    def build_index(self, hnsw_index=True):
        return self

    def attach_partition(self):
        return self

    def cleanup(self):
        with Session(self.engine) as session:
            session.execute(
                sa.text("DELETE FROM image_vector WHERE dataset_id = :dataset_id"),
                {"dataset_id": self.dataset_id}
            )
        return self
