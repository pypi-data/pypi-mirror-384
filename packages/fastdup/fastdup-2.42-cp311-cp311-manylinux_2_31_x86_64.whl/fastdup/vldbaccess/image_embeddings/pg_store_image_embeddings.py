import logging
import math
from typing import Optional
from uuid import UUID

from pathlib import Path

from sqlalchemy import Engine
import sqlalchemy as sa
from sqlalchemy.orm import Session

from fastdup.vl.common import logging_init
from fastdup.vl.common.settings import Settings
from fastdup.vl.utils.useful_decorators import timed
from fastdup.vldbaccess.image_embeddings.abstract_image_embeddings import AbstractImageEmbeddings, load_annotations, load_index

logger = logging_init.get_vl_logger(__name__)


class PGStoreImageEmbeddings(AbstractImageEmbeddings):

    def __init__(self, engine: Engine, dataset_id: UUID, index_path: Optional[Path] = None):
        super().__init__(engine, dataset_id, index_path)
        self.records = 0

    def _store_data(self, path, id_column: str = "image_id", is_image=True):
        from pgvector.psycopg import register_vector
        logger.info("Storing embeddings")
        partition_name = self.get_partition_name()
        numpy_index = load_index(path)
        annotations = load_annotations(path)

        with Session(self.engine) as session:
            with session.begin():
                session.execute(
                    sa.text(
                        f"CREATE TABLE IF NOT EXISTS {partition_name} "
                        f"(LIKE {self.get_table_name()} INCLUDING DEFAULTS INCLUDING CONSTRAINTS);")
                )
                session.execute(sa.text(f"ALTER TABLE {partition_name} ALTER COLUMN embedding SET STORAGE PLAIN"))
        with Session(self.engine) as session:
            conn = session.connection().connection.dbapi_connection
            register_vector(conn)
            with conn.cursor() as cur:
                with cur.copy(
                        f"COPY {partition_name} (dataset_id, media_id, is_image, embedding) FROM STDIN WITH (FORMAT BINARY)"  #
                ) as copy:
                    copy.set_types(["uuid", "uuid", "bool", "vector"])
                    for i, (image_id, embedding) in enumerate(zip(annotations[id_column], numpy_index)):
                        copy.write_row((self.dataset_id, UUID(image_id), is_image, embedding))
                        if i and i % 10000 == 0:
                            logger.debug("progress: %d/%d" % (i, len(numpy_index)))
            session.commit()
        self.records += len(numpy_index)

    @timed(context_keys=["self.dataset_id"])
    def build_index(self, hnsw_index=True):
        partition_name = self.get_partition_name()
        records = self.records
        if records > 1_000_000:
            lists = math.floor(math.sqrt(records))
        else:
            lists = math.floor(records / 1000)

        with Session(self.engine) as session:
            with session.begin():
                maintenance_work_mem_gb = Settings.PGVECTOR_MAINTENANCE_WORK_MEM_GB
                max_parallel_maintenance_workers = Settings.PGVECTOR_MAX_PARALLEL_MAINTENANCE_WORKERS
                if maintenance_work_mem_gb and isinstance(maintenance_work_mem_gb, int):
                    session.execute(
                        sa.text(f"SET maintenance_work_mem = '{maintenance_work_mem_gb}GB';")
                    )
                if max_parallel_maintenance_workers and isinstance(max_parallel_maintenance_workers, int):
                    session.execute(
                        sa.text(f"SET max_parallel_maintenance_workers = {max_parallel_maintenance_workers};")
                    )

                if hnsw_index:
                    session.execute(sa.text(
                        f"CREATE INDEX ON {partition_name} USING hnsw "
                        f"(embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);"
                    ))
                else:
                    session.execute(sa.text(
                        f"CREATE INDEX ON {partition_name} USING ivfflat "
                        f"(embedding vector_cosine_ops) WITH (lists = {lists});"
                    ))
        return self

    def attach_partition(self):
        with Session(self.engine) as session:
            with session.begin():
                partition_name = self.get_partition_name()
                session.execute(sa.text(
                    f"ALTER TABLE {self.get_table_name()} ATTACH PARTITION {partition_name} "
                    f"FOR VALUES IN ('{self.dataset_id}');")
                )
        return self

    def cleanup(self):
        partition_name = self.get_partition_name()
        with Session(self.engine) as session:
            with session.begin():
                partition_exists: int = session.execute(
                    sa.text('SELECT count(*) '
                            'FROM pg_catalog.pg_inherits '
                            'WHERE inhrelid::regclass::text=:partition_name'),
                    {"partition_name": partition_name}
                ).one()[0]
                if partition_exists:
                    session.execute(
                        sa.text(f'ALTER TABLE {self.get_table_name()} DETACH PARTITION {partition_name};'))
                    session.execute(sa.text(f"DROP TABLE IF EXISTS {partition_name}"))
        return self
