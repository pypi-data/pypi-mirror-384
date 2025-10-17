"""
Configure Python SDK

pip install --upgrade sentry-sdk
Import and initialize the Sentry SDK early in your application's setup:

import sentry_sdk
sentry_sdk.init(
    dsn="https://d79dd3832b804d63921b8858ad766e43@o4504135122944000.ingest.sentry.io/4505317881020416",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)

"""

import hashlib
import os
import platform
import sys
import time
import traceback
import uuid
from functools import wraps

import sentry_sdk
from sentry_sdk import capture_exception, capture_event
from sentry_sdk import metrics
from typing import Dict, Any

from fastdup.vl.common.settings import Settings

try:
    from fastdup.definitions import VERSION__ as FASTDUP_VERSION
    VERSION = FASTDUP_VERSION
except ImportError as e:
    VERSION = ''

#get a random token based on the machine uuid
token = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()
unit_test = None

sentry_initialized: bool = False


def exception_err_info():
    return traceback.format_exception(*sys.exc_info())


def find_certifi_path():
    try:
        import certifi
        return os.path.join(os.path.dirname(certifi.__file__), 'cacert.pem')
    except Exception as ex:
        print('Failed to find certifi', ex)
    return None


def init_sentry(environment: str, version: str = VERSION, step: str = None):
    """
    Init a sentry client for capturing errors.

    :param environment: Environment name for sentry filtering
    :param version: Configurable
    :param step: Pipeline step


    """
    global sentry_initialized
    if sentry_initialized:
        return

    global unit_test

    if not Settings.SENTRY_OPT_OUT:

        if platform.system() == 'Darwin':
            # fix CA certficate issue on latest MAC models
            path = find_certifi_path()
            if path is not None:
                if 'SSL_CERT_FILE' not in os.environ:
                    os.environ["SSL_CERT_FILE"] = path
                if 'REQUESTS_CA_BUNDLE' not in os.environ:
                    os.environ["REQUESTS_CA_BUNDLE"] = path

        sentry_sdk.init(
            dsn=Settings.SENTRY_PROJ,
            debug='SENTRY_DEBUG' in os.environ,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=1,
            include_local_variables=True,
            release=version,  # fastdup version
            # default_integrations=False,
            environment=environment,
            attach_stacktrace=True,
        )
        unit_test = 'UNIT_TEST' in os.environ

        # Global tags for the run
        sentry_sdk.set_tag('step', step)
        sentry_sdk.set_tag("production", os.getenv('VL_PRODUCTION_NAME', 'Default'))

        sentry_sdk.set_tag("unit_test", unit_test)
        sentry_sdk.set_tag("token", token)
        sentry_sdk.set_tag("platform", platform.platform().replace('\n',''))
        sentry_sdk.set_tag("platform.version", platform.version().replace('\n',''))
        sentry_sdk.set_tag("python", sys.version.replace('\n',''))
        sentry_sdk.set_tag("dataset_id", os.getenv('DATASET_ID', ''))
        sentry_sdk.set_tag("execution_id", os.getenv('EXECUTION_ID', ''))

        try:
            filename = os.path.join(os.environ.get('HOME', '/tmp'), ".token")
            with open(filename, "w") as f:
                f.write(token)
        except:
            pass

    sentry_initialized = True


def sentry_capture_exception(section, exception, warn_only=False, extra="", extra_tags=None):
    """
    @param section:
    @param exception:
    @param step:
    @param warn_only:
    @param extra:
    @param extra_tags: Dictionary of {'tag_name': 'tag_value'} values for sentry tags

    """
    if not warn_only:
        traceback.print_exc()
    if not Settings.SENTRY_OPT_OUT:
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("section", section)

            if extra != "":
                scope.set_tag("extra", extra)
            if extra_tags and isinstance(extra_tags, dict):
                for tag_name, tag_value in extra_tags.items():
                    scope.set_tag(tag_name, tag_value)
            capture_exception(exception, scope=scope)


def sentry_capture_event(message: str, level: str = 'info', extra: Dict[str, Any] = {}, tags: Dict[str, Any] = {}) -> None:
    capture_event({'message': message, 'level': level, 'extra': extra, 'tags': tags})


def sentry_performance_capture(section: str, start_time: float, extra_tags: dict = None):
    """
    Capture a successful run
    :param section: Name to be recorded
    :param start_time: Time of run start for logging
    :param extra_tags: Dictionary of {'tag_name': 'tag_value'} values for sentry tags
    """
    if not Settings.SENTRY_OPT_OUT:
        try:
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("section", section)
                if isinstance(extra_tags, dict):
                    for tag_name, tag_value in extra_tags.items():
                        scope.set_tag(tag_name, tag_value)

                elapsed = int((time.time() - start_time) * 1000)
                sentry_sdk.capture_message(f"{section} took {elapsed} ms", scope=scope)
        finally:
            sentry_sdk.flush(timeout=5)


def send_file(file_description: str, filepath: str):
    if not Settings.SENTRY_OPT_OUT:
        with sentry_sdk.push_scope() as scope:
            scope.add_attachment(path=filepath)
            sentry_sdk.capture_message(file_description, scope=scope)


def capture_breadcrumb(data: dict):
    """
    Capture a breadcrumb (intermediate output) during run
    """
    if not Settings.SENTRY_OPT_OUT:
        breadcrumb = {'type':'debug', 'category':'setup', 'message':'snapshot', 'level':'info', 'timestamp':time.time()}
        breadcrumb['data'] = data
        sentry_sdk.add_breadcrumb(breadcrumb)


def sentry_exception_only_decorator(func):
    @wraps(func)
    def inner_function(*args, **kwargs):
        try:
            start_time = time.time()
            ret = func(*args, **kwargs)
            return ret

        except Exception as ex:
            sentry_capture_exception(f"{func.__name__}", ex)
            raise ex
    return inner_function


def sentry_performance_capture_decorator(func):
    @wraps(func)
    def inner_function(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
            return ret

        except Exception as ex:
            sentry_capture_exception(f"{func.__name__}", ex)
            raise ex
    return inner_function


def flatten_dict(dictionary, parent_key='', sep='_', skip_key_list=()):
    flattened_dict = {}
    for k, v in dictionary.items():
        if k in skip_key_list: continue
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            flattened_dict.update(flatten_dict(v, new_key, sep=sep))
        else:
            flattened_dict[new_key] = v
    return flattened_dict


def metrics_increment(key: str):
    if not Settings.SENTRY_OPT_OUT:
        metrics.incr(
            key=key,
            value=1,
        )


def metrics_distribution(key: str, value: int, unit: str = "second"):
    if not Settings.SENTRY_OPT_OUT:
        metrics.distribution(
            key=key,
            value=value,
            unit=unit
        )
