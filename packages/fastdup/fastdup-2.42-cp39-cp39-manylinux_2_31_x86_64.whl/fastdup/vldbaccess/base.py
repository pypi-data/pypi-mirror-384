import tempfile
import uuid
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from uuid import UUID

import polars as pl
import sqlalchemy as sa
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from fastdup.vl.common.logging_init import get_vl_logger
from fastdup.vl.common.settings import Settings
from fastdup.vl.utils import formatting
from fastdup.vl.utils.useful_decorators import log_exception_with_args, timed
from fastdup.vldbaccess.connection_manager import get_session
from fastdup.vldbaccess.event_dao import EventDAO
from fastdup.vldbaccess.models import events

if not Settings.IS_FASTDUP:
    from psycopg.sql import SQL, Identifier

logger = get_vl_logger(__name__)

column_cast_handlers = {
    "duckdb": {
        "similarity_clusters": {
            "similarity_threshold": pl.Utf8
        }
    }
}

column_override_handlers = {
    "duckdb": {
        "labels": {
            "type": lambda x: x.name if isinstance(x, Enum) else x,
            "bounding_box": lambda x: (x.replace("{", "[").replace("}", "]")) if x else None
        },
        "objects_to_images": {
            "bounding_box": lambda x: (x.replace("{", "[").replace("}", "]")) if x else None
        }
    },
    "postgresql": {
        "labels": {
            "type": lambda x: x.name if isinstance(x, Enum) else x,
        },
        "media_to_captions": {
            "caption": lambda x: x if x else "\"\"",  # TODO: find a better solution
        }
    }
}


class DatasetSourceType(str, Enum):
    UPLOAD = 'UPLOAD'
    PUBLIC_BUCKET = 'PUBLIC_BUCKET'  # left for backward compatibility while testing
    BUCKET = 'BUCKET'
    VL = 'VL'


class DatasetStatus(str, Enum):
    INITIALIZING = 'INITIALIZING'
    UPLOADING = 'UPLOADING'
    SAVING = 'SAVING'
    INDEXING = 'INDEXING'
    READY = 'READY'
    FATAL_ERROR = 'FATAL_ERROR'

    def __repr__(self):
        return self.value.lower().replace('_', " ")


class AccessOperation(str, Enum):
    READ = 'READ'
    LIST = 'LIST'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    MANAGE_ACCESS = 'MANAGE_ACCESS'
    SHARE_DATASETS = 'SHARE_DATASETS'


class Severity(Enum):
    HIGH = 0
    MEDIUM = 1
    LOW = 2

    def display_name(self):
        return self.name.lower()


class SeverityCount(BaseModel):
    severity: Severity
    n_images: int

    # calculated fields
    n_images_display_value: int = 0
    severity_display_name: str = ''
    percentage: float = 0

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True

    @classmethod
    @validator("n_images_display_value", always=True)
    def _n_images_display_value(cls, _v, values, **_kwargs):
        return formatting.sizeof_fmt(values['n_images'], suffix='', precision=0, k_size=1000)

    @classmethod
    @validator("severity_display_name", always=True)
    def _severity_display_name(cls, _v, values, **_kwargs):
        return values['severity'].display_name()

    def percentage_relative_to(self, total: int):
        self.percentage = self.n_images / total * 100

    def dict(self, **kwargs):
        """Override dict method to ensure proper serialization"""
        data = super().dict(**kwargs)
        data['severity'] = self.severity.value if hasattr(self.severity, 'value') else str(self.severity)
        return data


class SampleDataset(str, Enum):
    SAMPLE = 'SAMPLE'
    DEFAULT_SAMPLE = 'DEFAULT_SAMPLE'

    @staticmethod
    @log_exception_with_args
    def from_optional_str(value: Optional[str]) -> Optional["SampleDataset"]:
        if value is None:
            return None
        return SampleDataset[value]


def get_table_columns(table_name: str, session: Session) -> Dict[str, int]:
    table_columns: dict[str, int] = dict(
        session.execute(
            sa.text("""
                SELECT column_name, ordinal_position 
                FROM information_schema.columns
                WHERE table_name = :table_name AND table_schema = CURRENT_SCHEMA();
            """),
            {"table_name": table_name}).all()
    )
    return table_columns


@timed
def dataframe_to_table(df: pl.DataFrame, table_name: str, columns=None):
    logger.info("Dumping table %s of length %s", table_name, len(df))
    if len(df.columns) == 0 or len(df) == 0:
        logger.warning("attempting to dump an empty dataframe %s", table_name)
        return None

    if columns is not None:
        for c in columns:
            assert c in df.columns, f"Failed to find column {c} in {df.columns} {df.head()}"

        df = df[columns]
    with get_session(autocommit=True) as session:
        dialect = session.bind.dialect.name

        table_columns = get_table_columns(table_name, session)
        sorted_df = df[sorted(df.columns, key=lambda x: table_columns.get(x, -1))]

        for col, cast_type in column_cast_handlers.get(dialect, {}).get(table_name, {}).items():
            sorted_df = sorted_df.with_columns(
                pl.col(col).cast(cast_type).alias(col)
            )
        for col, handler in column_override_handlers.get(dialect, {}).get(table_name, {}).items():
            sorted_df = sorted_df.with_columns(
                pl.col(col).map_elements(handler, return_dtype=sorted_df.schema[col]).alias(col))

        if dialect == "postgresql":
            assert len(sorted_df), f"Got dataframe with zero rows"
            with tempfile.NamedTemporaryFile(delete=True) as tmp:
                tmp_path = Path(tmp.name)
                sorted_df.write_csv(tmp_path, include_header=False, )
                with (
                    session.connection().connection.dbapi_connection.cursor() as cur,
                    cur.copy(SQL(r"COPY {table_name} ({fields}) FROM STDIN WITH (FORMAT CSV)").format(
                        table_name=Identifier(table_name),
                        fields=SQL(',').join([Identifier(col) for col in sorted_df.columns]))
                    ) as copy
                ):
                    while data := tmp.read(8192):
                        try:
                            copy.write(data)
                        except Exception as ex:
                            tmp.seek(0)
                            head = [next(tmp) for _ in range(4)]
                            logger.exception(
                                "%s Failed writing dataframe from file to table %s. File head:\n %s\n",
                                ex, table_name, head
                            )
                            raise ex
        elif dialect == "duckdb":
            assert len(sorted_df), f"Got dataframe with zero rows"
            fields = ','.join(['"%s"' % w for w in sorted_df.columns])
            # Note, due to change in duckdb v1 and up, sorted_df is no longer visible for sqlalchemy so
            # we had to register it into the connection explicitly.
            conn = session.connection().connection
            conn.register("sorted_df", sorted_df)
            #for debugging only
            #result = conn.execute("SHOW TABLES").fetchall()
            #print(result)
            try:
                session.execute(sa.text(f"INSERT INTO {table_name}({fields}) SELECT * FROM sorted_df"))
            except Exception as e:
                logger.exception(f"Failed to insert {sorted_df.head()} {fields}")
                raise e

        else:
            raise NotImplementedError(f"Copy is not supported for {dialect} connection")

    logger.info(f"Finished dumping table %s of length %s", table_name, len(df))
    return None


class BaseDB:

    @staticmethod
    @log_exception_with_args
    def _grant_access(
            conn: Session,
            dataset_id: UUID,
            user_id: UUID,
            ops: List[AccessOperation]
    ):
        op: AccessOperation
        for op in ops:
            conn.execute(sa.text("""
                INSERT INTO
                    access(subject_id, object_id, operation)
                VALUES
                    (:user_id, :dataset_id, :op)
                ON CONFLICT DO NOTHING
                ;"""), {
                "user_id": user_id,
                "dataset_id": dataset_id,
                "op": op.name}
                         )

    @staticmethod
    @log_exception_with_args
    def _grant_access_to_all(
            conn: Session,
            dataset_id: UUID,
            ops: List[AccessOperation]
    ):
        op: AccessOperation
        for op in ops:
            conn.execute(sa.text("""
                INSERT INTO access(subject_id, object_id, operation) (
                    SELECT id, :dataset_id, :op FROM users
                )
                ON CONFLICT DO NOTHING
                ;"""), {"dataset_id": dataset_id, "op": op.name})

    @staticmethod
    def _grant_access_to_group(
            conn: Session,
            dataset_id: UUID,
            group_name: str,
            ops: List[AccessOperation]
    ):
        op: AccessOperation
        for op in ops:
            conn.execute(sa.text("""
                        INSERT INTO
                            access(subject_id, object_id, operation)
                        SELECT
                            id, :dataset_id, :op
                        FROM
                            user_groups
                        WHERE
                            name = :group_name
                        ON CONFLICT DO NOTHING
                        ;"""),
                         {
                             "group_name": group_name,
                             "dataset_id": dataset_id,
                             "op": op.name
                         }
                         )

    @staticmethod
    @log_exception_with_args
    def _remove_access(
            conn: Session,
            dataset_id: UUID,
            user_id: UUID,
            ops: List[AccessOperation]
    ):
        op: AccessOperation
        for op in ops:
            conn.execute(sa.text("""
                DELETE FROM
                    access
                WHERE
                    subject_id = :user_id
                    AND object_id = :dataset_id
                    AND operation = :op
                ;"""), {"user_id": user_id, "dataset_id": dataset_id, "op": op.name})

    @staticmethod
    @log_exception_with_args
    def _get_system_user_id(conn: Session) -> UUID:
        res = conn.execute(sa.text("""
            SELECT
                id
            FROM
                users
            WHERE
                user_identity = 'system'
                AND identity_provider = 'system'
            ;""")).one()
        return res[0]

    @staticmethod
    @log_exception_with_args
    def _get_sample_dataset_ids(conn: Session) -> Tuple[List[UUID], List[UUID]]:
        default_samples = []
        samples = []

        query_res = conn.execute(sa.text("""
            SELECT
                id, sample
            FROM
                datasets
            WHERE
                sample IS NOT NULL
                AND NOT deleted
            ;""")).all()
        for tup in query_res:
            if tup[1] == SampleDataset.DEFAULT_SAMPLE.name:
                default_samples.append(tup[0])
            elif tup[1] == SampleDataset.SAMPLE.name:
                samples.append(tup[0])

        return default_samples, samples

    @staticmethod
    @log_exception_with_args
    def execute_batch_stmt(stmt: str, batch: List) -> int:
        if len(batch):
            try:
                with get_session(autocommit=True) as session:
                    res = session.execute(sa.text(stmt), batch)
                    return res.rowcount
            except Exception as e:
                logger.error("Error in Batch Statement: %s", e, exc_info=True)
                raise e
        return 0

    @staticmethod
    def is_access_granted(subject_id: UUID, object_id: UUID, op: AccessOperation) -> bool:
        with get_session() as session:
            params = {
                'subject_id': subject_id,
                'object_id': object_id,
                'op': op.name
            }
            res = session.execute(sa.text("""
                SELECT
                    1
                FROM
                    access
                WHERE
                    subject_id = :subject_id
                AND
                    object_id = :object_id
                AND
                    operation = :op
            """), params).scalars().one_or_none()
            return res and res == 1

    @staticmethod
    @log_exception_with_args
    def _handle_dataset_status_event(dataset_id: UUID, ctx: dict):
        if 'status' not in ctx:
            return

        if ctx['status'] == DatasetStatus.FATAL_ERROR:
            EventDAO.store(events.FatalDatasetStatus(dataset_id=dataset_id,
                                                     status=str(ctx['status']),
                                                     progress=0,
                                                     error_reference_id=uuid.uuid1(),
                                                     reason=ctx.get('fatal_error_msg',
                                                                    'Dataset creation failed')))

        else:
            EventDAO.store(events.DatasetStatus(dataset_id=dataset_id, status=str(ctx['status']), progress=0))
