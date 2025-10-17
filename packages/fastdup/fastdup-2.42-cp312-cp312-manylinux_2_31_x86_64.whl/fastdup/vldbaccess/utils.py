import asyncio
import functools

from fastdup.vldbaccess.base import AccessOperation
from fastdup.vldbaccess.dataset import DatasetDB
from fastdup.vldbaccess.models.exploration_context import ExplorationContext
from fastdup.vldbaccess.user import UserDB

DEFAULT_OPERATIONS = [AccessOperation.READ]

def can_access_dataset(exc: Exception, operations=None):
    if operations is None:
        operations = DEFAULT_OPERATIONS
    def _decor(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context: ExplorationContext = kwargs['context']
            if not UserDB.check_authorized_user(context.user, context.dataset_id, operations):
                raise exc
            res = func(*args, **kwargs)
            return res

        @functools.wraps(func)
        async def awrapper(*args, **kwargs):
            context: ExplorationContext = kwargs['context']
            if not UserDB.check_authorized_user(context.user, context.dataset_id, operations):
                raise exc
            res = await func(*args, **kwargs)
            return res

        if asyncio.iscoroutinefunction(func):
            return awrapper
        else:
            return wrapper

    return _decor
