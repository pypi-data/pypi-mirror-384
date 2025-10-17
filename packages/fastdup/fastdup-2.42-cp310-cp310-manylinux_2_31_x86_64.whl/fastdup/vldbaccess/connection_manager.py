import sys
from contextlib import contextmanager, asynccontextmanager

from typing import Optional
from collections.abc import Iterator, AsyncIterator
from urllib.parse import urlparse, parse_qs, urlencode

import duckdb_engine
import sqlalchemy as sa
from sqlalchemy.event import listens_for

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from fastdup.vl.common.logging_init import get_vl_logger
from fastdup.vl.common.settings import Settings

from fastdup.vl.utils.aws_secrets import get_secret
from fastdup.vldbaccess.duckdb_async_dialect import AsyncDialect

duckdb_engine.Dialect.get_async_dialect_cls = lambda cls: AsyncDialect

__engine: Optional[sa.Engine] = None
__async_engine: Optional[AsyncEngine] = None
__dialect: Optional[str] = None


logger = get_vl_logger(__name__)
HOUR_S = 60 * 60


def log_pool_status(pool: sa.Pool):
    if pool.checkedin() > 5:
        logger.info(pool.status())


def get_pg_uri() -> str:
    pg_uri = Settings.PG_URI
    pg_secret = Settings.PG_SECRET

    if not pg_uri and not pg_secret:
        logger.error("No PG_URI nor PG_SECRET variable supplied")
        print("No PG_URI nor PG_SECRET variable supplied", file=sys.stderr)
        sys.exit(1)
    elif pg_uri is None:
        pg_uri = get_secret(pg_secret, 'pg_uri')
    uri = urlparse(pg_uri)
    if uri.scheme == 'postgresql':
        pg_uri = (
            uri
            ._replace(scheme="postgresql+psycopg")
            ._replace(query=urlencode(parse_qs(uri.query) | {"application_name": Settings.ENV_NAME}))
        ).geturl()
    return pg_uri


def init_engine() -> sa.Engine:
    logger.debug("Initializing sync engine with PG_SECRET: %s, PG_URI: %s",
                 Settings.PG_SECRET, Settings.PG_URI)
    global __engine
    __engine = sa.create_engine(
        get_pg_uri(), pool_size=Settings.MAX_PG_CONNECTION_POOL_SIZE, poolclass=sa.QueuePool, pool_recycle=HOUR_S
    )

    @listens_for(__engine, "connect", named=True)
    def on_connect_register_vector(dbapi_connection, **kwargs):
        if dbapi_connection.__module__ == "psycopg":
            from pgvector.psycopg import register_vector
            register_vector(dbapi_connection)

    return __engine


def init_async_engine() -> AsyncEngine:
    global __async_engine
    logger.debug("Initializing async engine with PG_SECRET: %s, PG_URI: %s",
                 Settings.PG_SECRET, Settings.PG_URI)
    __async_engine = create_async_engine(
        get_pg_uri(),
        pool_size=Settings.MAX_PG_CONNECTION_POOL_SIZE,
        poolclass=sa.AsyncAdaptedQueuePool,
        pool_recycle=HOUR_S
    )
    @listens_for(__async_engine.sync_engine, "connect", named=True)
    def on_connect_register_vector(dbapi_connection, **kwargs):
        if not dbapi_connection.__module__ == "duckdb_engine" and dbapi_connection.connection.__module__ == 'psycopg':
            from pgvector.psycopg import register_vector_async
            dbapi_connection.await_(register_vector_async(dbapi_connection.connection))

    return __async_engine


def close_connection_pool():
    global __engine
    if __engine is not None:
        __engine.dispose()
    __engine = None


async def close_async_connection_pool():
    global __async_engine
    if __async_engine is not None:
        await __async_engine.dispose()
    __async_engine = None


def reset_pool():
    global __async_engine
    global __dialect
    global __engine
    close_connection_pool()
    if __async_engine:
        try:
            close_async_connection_pool().send(None)
        except StopIteration as _e:
            pass

    __engine = None
    __async_engine = None
    __dialect = None


def get_engine() -> sa.Engine:
    if __engine is None:
        init_engine()
    assert __engine is not None
    return __engine


def get_async_engine() -> AsyncEngine:
    if __async_engine is None:
        init_async_engine()
    assert __async_engine is not None
    return __async_engine


@contextmanager
def get_session(autocommit=False, **kwargs) -> Iterator[Session]:
    with sessionmaker(bind=get_engine())() as session:
        if autocommit:
            session.begin()

        yield session
        if autocommit:
            session.commit()
        session.close()


@asynccontextmanager
async def get_async_session(autocommit=False, vector=False, **kwargs) -> AsyncIterator[AsyncSession]:
    async with async_sessionmaker(bind=get_async_engine())() as session:
        if autocommit:
            await session.begin()
        yield session
        if autocommit:
            await session.commit()
        await session.close()


def get_engine_dialect() -> str:
    global __dialect
    if __dialect is None:
        __dialect = get_engine().dialect.name
    return __dialect
