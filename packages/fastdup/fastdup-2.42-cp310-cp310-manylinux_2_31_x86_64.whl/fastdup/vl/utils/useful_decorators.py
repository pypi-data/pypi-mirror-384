import asyncio
import functools
import inspect
import textwrap
import time
import traceback
from typing import Optional, TYPE_CHECKING

from setproctitle import setproctitle
from starlette.responses import Response

from fastdup.vl.common.logging_init import get_vl_logger
from fastdup.vl.common.settings import Settings

if TYPE_CHECKING:
    from fastdup.vldbaccess.models.exploration_context import ExplorationContext

logger = get_vl_logger(__name__)



try:
    from fastdup.vl.utils.sentry import init_sentry, sentry_performance_capture
except ImportError:
    def _fake_function(*args, **kw):
        pass
    init_sentry = _fake_function
    sentry_performance_capture = _fake_function


if not Settings.DEPLOYMENT_REMOTE_ACCESS:
    init_sentry(environment=Settings.CUSTOMER_NAME, version='')


def _cache_header_by_tag_data(response: Response, kwargs: dict):
    tag_data = False
    context: Optional["ExplorationContext"] = kwargs.get('context', None)
    if context:
        tag_data = context.tags or context.untagged
    else:
        tag_data = bool(kwargs.get("tags"))
    if not tag_data:
        response.headers['Cache-Control'] = 'max-age=3600'


def cache_header_decorator(func):
    @functools.wraps(func)
    def wrapper(response: Response, *args, **kwargs):
        res = func(*args, **kwargs, response=response)
        _cache_header_by_tag_data(response, kwargs)
        return res

    @functools.wraps(func)
    async def awrapper(response: Response, *args, **kwargs):
        res = await func(*args, **kwargs, response=response)
        _cache_header_by_tag_data(response, kwargs)
        return res

    if asyncio.iscoroutinefunction(func):
        return awrapper
    else:
        return wrapper


def _generate_context(args, kwargs: dict, context_keys: list) -> Optional[dict]:
    if context_keys:
        context = {}
        for key in context_keys:
            _obj = kwargs
            key_part = None
            for key_part in key.split('.'):
                if isinstance(_obj, dict):
                    _obj = _obj.get(key_part)
                else:
                    _obj = getattr(_obj, key_part, None)
            else:
                if key_part is not None and _obj is not None:
                    context[key_part] = _obj
        return context
    return None


def _timed_pre_run(func):
    start = time.time()
    setproctitle(f'{func.__module__}.{func.__qualname__}')
    logger.info(f'Started {func.__module__}.{func.__qualname__}')
    return start


def _timed_post_run(func, start, context: Optional[dict[str, str]] = None):
    elapsed = int((time.time() - start) * 1000)
    elapsed_msg = f'Timing results: {func.__module__}.{func.__qualname__} took {elapsed} ms'
    logger.info(
        elapsed_msg, extra={
            "elapsed_ms": elapsed,
            "source": func.__qualname__,
            "context": context
        })
    if elapsed > 5000:  # send update for execution longer than 5 seconds, as we are paying for each call better reduce insignificant function calls
        sentry_performance_capture(elapsed_msg, start_time=start)


def timed(*args, context_keys=None):

    def _timed_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = _timed_pre_run(func)
            res = func(*args, **kwargs)
            _timed_post_run(
                func, start, _generate_context(
                    args, kwargs, context_keys
                )
            )
            return res

        @functools.wraps(func)
        async def awrapper(*args, **kwargs):
            start = _timed_pre_run(func)
            res = await func(*args, **kwargs)
            _timed_post_run(
                func, start, _generate_context(
                    args, kwargs, context_keys
                )
            )
            return res

        if asyncio.iscoroutinefunction(func):
            return awrapper
        else:
            return wrapper

    if context_keys is None and len(args) == 1 and callable(args[0]):
        return _timed_decorator(args[0])

    return _timed_decorator


def public_api(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    @functools.wraps(func)
    async def awrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return awrapper
    else:
        return wrapper


def log_exception_with_args(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            func_args = inspect.signature(func).bind(*args, **kwargs).arguments
            extra = {
                'exception_type': type(e).__qualname__,
                'exception_message': str(e),
                'exception': e.with_traceback,
                'func': f'{func.__module__}.{func.__qualname__}',
                'arguments': func_args,
            }
            logger.exception(e, extra=extra)
            raise
    return wrapper


def arg_logger(func):
    """
    Nicely log the fully qualified function name, the arguments and the call stack.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func_args = inspect.signature(func).bind(*args, **kwargs).arguments
            msg = textwrap.dedent(
                f"""
                func:
                    {func.__module__}.{func.__qualname__}
                arguments:
                    {', '.join(k + '=' + str(func_args[k]) for k in func_args)}
                stack:
                """
            ) + ''.join(s for s in traceback.format_stack())
            logger.info(msg)
            return func(*args, **kwargs)
        except Exception as e:
            raise

    return wrapper
