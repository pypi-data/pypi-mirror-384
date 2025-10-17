import abc
from typing import Optional
from uuid import UUID

import numpy as np
import pandas as pd
from pathlib import Path

from sqlalchemy import Engine

from fastdup.vl.common import logging_init
from fastdup.vl.utils.useful_decorators import timed

logger = logging_init.get_vl_logger(__name__)


def load_annotations(annotation_path: Path, file_name='full_annot.pkl.gz') -> pd.DataFrame:
    if annotation_path.is_dir():
        annotation_path = annotation_path.joinpath(file_name)
    return pd.read_pickle(annotation_path)


def load_index(index_path: Path) -> np.ndarray:
    import fastdup
    _file_list, embeddings_matrix = fastdup.load_binary_feature(str(index_path))
    return embeddings_matrix


class AbstractImageEmbeddings(metaclass=abc.ABCMeta):
    cosine_distance = True

    def __init__(self, engine: Engine, dataset_id: UUID, index_path: Optional[Path] = None) -> None:
        self.engine = engine
        self.dataset_id = dataset_id
        self.index_path = index_path

    def _store_data(self, path, id_column: str = "image_id", is_image=True):
        raise NotImplementedError()

    def attach_partition(self):
        raise NotImplementedError()

    def build_index(self, hnsw_index=True):
        raise NotImplementedError()

    @timed(context_keys=["self.dataset_id"])
    def store_data(self):
        index_path = self.index_path
        assert index_path is not None
        self._store_data(id_column="image_uuid", is_image=True, path=index_path.joinpath("images/"))
        objects_path = index_path.joinpath("objects/")
        if objects_path.exists():
            self._store_data(id_column="object_uuid", is_image=False, path=objects_path)
        else:
            logger.info("No objects data found for %s skipping object embeddings ", self.dataset_id)
        return self

    def get_table_name(self) -> str:
        return f"image_vector"

    def get_partition_name(self) -> str:
        return f"{self.get_table_name()}_{str(self.dataset_id).replace('-', '_')}"

    def cleanup(self):
        raise NotImplementedError()
