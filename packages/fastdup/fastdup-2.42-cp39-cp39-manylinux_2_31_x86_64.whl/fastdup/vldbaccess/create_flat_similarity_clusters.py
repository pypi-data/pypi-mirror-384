from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session

from fastdup.vl.common import logging_helpers
from fastdup.vl.common.settings import Settings
from fastdup.vldbaccess import sql_template_utils
from fastdup.vldbaccess.connection_manager import get_session
from fastdup.vldbaccess.dataset import DatasetDB
from fastdup.vldbaccess.sql_template_utils import QueryModule


def create_and_fill_partition(dataset_id: UUID):
    with get_session(autocommit=True) as session:
        dialect = session.bind.dialect.name
        if dialect == "postgresql":
            create_and_fill_partition_pg(dataset_id, session)
        elif dialect == "duckdb":
            create_and_fill_partition_duckdb(dataset_id, session)
        else:
            raise NotImplementedError(f"Unsupported dialect {dialect}")


def _create_and_fill_partition(dataset_id: UUID, partition_name, session: Session):
    ctx = {'dataset_id': dataset_id}

    for query_file in [
        "create_temp_flat_image_issues.jinja2",
        "fill_temp_flat_image_issues_images.jinja2",
        "fill_temp_flat_image_issues_objects.jinja2",
        "create_temp_flat_labels.jinja2",
        "fill_temp_flat_labels_images.jinja2",
        "fill_temp_flat_labels_objects.jinja2",
        "create_flat_similarity_cluster_images.jinja2",
        "create_flat_similarity_cluster_objects.jinja2"
    ]:
        query = sql_template_utils.render(QueryModule.DATASETS, query_file, partition_name=partition_name)
        logging_helpers.log_sql_query(__name__, query_file, query, ctx, )
        session.execute(
            sa.text(query), ctx
        )


def create_and_fill_partition_duckdb(dataset_id: UUID, session: Session):
    # TODO: remove duplication
    partition_name = "flat_similarity_clusters"
    _create_and_fill_partition(dataset_id, partition_name, session)

    # Skip FTS index creation to avoid extension download issues
    # The FTS functionality has been disabled to prevent DuckDB extension loading errors
    # Original FTS creation code commented out:
    # session.execute(
    #     sa.text("""
    #     PRAGMA create_fts_index(
    #         flat_similarity_clusters, image_or_object_id, caption, labels, vl_labels, stemmer='porter',
    #         stopwords='english', ignore='(\\.|[^a-z])+',
    #         strip_accents=1, lower=1, overwrite=1
    #     );
    #     """)
    # )


def create_and_fill_partition_pg(dataset_id: UUID, session: Session):
    partition_name = DatasetDB.flat_partition_name(dataset_id)
    check_name = f'{partition_name}_chk'
    ctx = {'dataset_id': dataset_id}

    # drop partition if exists
    with session.begin(nested=True):
        DatasetDB.remove_partition(dataset_id, session)
    # create partition
    with session.begin(nested=True):
        session.execute(
            sa.text(f"""
            CREATE TABLE {partition_name}
            (LIKE flat_similarity_clusters INCLUDING DEFAULTS INCLUDING CONSTRAINTS);
            """)
        )
        session.execute(sa.text(f"""
            ALTER TABLE {partition_name} ADD CONSTRAINT {check_name} CHECK (dataset_id='{dataset_id}')
            """), {'dataset_id': dataset_id})
    # insert into partition
    with session.begin(nested=True):
        session.execute(sa.text("SET enable_nestloop TO off;"))
        _create_and_fill_partition(dataset_id, partition_name, session)
        session.execute(sa.text("SET enable_nestloop TO on;"))

    with session.begin(nested=True) as _tx:
        session.execute(
            sa.text("""
            ALTER TABLE flat_similarity_clusters ATTACH PARTITION {partition_name} FOR VALUES IN ('{dataset_id}');
            """.format(partition_name=partition_name, dataset_id=dataset_id))
        )
