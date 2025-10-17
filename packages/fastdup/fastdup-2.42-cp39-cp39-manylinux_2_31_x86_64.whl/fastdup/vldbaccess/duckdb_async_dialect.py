from duckdb_engine import Dialect
from sqlalchemy import pool, util


class AsyncDialect(Dialect):
    is_async = True
    supports_statement_cache = False

    @classmethod
    def get_pool_class(cls, url):
        async_fallback = url.query.get("async_fallback", False)

        if util.asbool(async_fallback):
            return pool.FallbackAsyncAdaptedQueuePool
        else:
            return pool.AsyncAdaptedQueuePool
