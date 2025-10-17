import contextlib
import logging
import textwrap
import time
from typing import Union, Optional

from sqlalchemy import TextClause, text

from sqlalchemy.exc import ProgrammingError
from fastdup.vldbaccess import connection_manager
from fastdup.vl.common.settings import Settings

if not Settings.IS_FASTDUP:
    from psycopg import ClientCursor


def log_sql_query(
        name: str, query_name: str, query: Union[TextClause, str], params: dict, level=logging.DEBUG,
        duration: Optional[float] = None
):
    logger = logging.getLogger(f"sql.{name}")
    if logger.isEnabledFor(level):
        if isinstance(query, str):
            query = text(query)
        with connection_manager.get_session() as session:
            rendered_query = str(query.compile(dialect=session.bind.engine.dialect))
            dialect = connection_manager.get_engine_dialect()
            if dialect == "postgresql":
                conn = session.connection().connection.dbapi_connection
                query_string = ClientCursor(conn).mogrify(rendered_query, params)
            else:
                # TODO: find a better option
                query_string = rendered_query % params
            if duration is not None:
                duration_txt = " query took %ss to run " % duration
            else:
                duration_txt = ""
            log_msg = "Query: %s %s: \n--\n%s\n--"
            logger.log(
                level,
                log_msg,
                query_name, duration_txt, textwrap.dedent(query_string),
            )
        return query_string
    else:
        return ""


@contextlib.contextmanager
def log_sql_query_time(
        name: str,
        query_name: str,
        query: Union[TextClause, str],
        params: dict,
        level=logging.DEBUG,
        duration_seconds: float = 0.0
):
    t0 = time.monotonic()
    try:
        yield
    except ProgrammingError as e:
        log_sql_query(name, query_name, query, params, logging.ERROR, duration=None)
        raise e
    duration = time.monotonic() - t0
    if duration > duration_seconds:
        log_sql_query(name, query_name, query, params, level, duration=duration)
