import logging.config
from pathlib import Path
from typing import Optional

import yaml
from fastdup.vl.common.settings import Settings

_LOGGING_INITIALIZED = False

def _init_logging() -> None:
    """
    Initialize logging when running pure python.
    Other execution methods (uvicorn etc.) initialization may differ.
    """
    config_file: Path = Settings.VL_HOME / Settings.LOGGING_CONFIG_FILE
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                logging_config = yaml.safe_load(f)
                logging.config.dictConfig(logging_config)

                _configure_logging_for_no_access_deployment()
        except Exception as e:
            logging.exception(e)
            logging.basicConfig(level=Settings.LOG_LEVEL)
    else:
        logging.basicConfig(level=Settings.LOG_LEVEL)

def _configure_logging_for_no_access_deployment():
    if not Settings.DEPLOYMENT_REMOTE_ACCESS:
        from logzio.handler import ExtraFieldsLogFilter
        
        if logzio_logger := logging.getLogger('logzio'):
            if logzio_logger.handlers:
                logzio_handler: logging.Handler = logzio_logger.handlers[0]
                logging.getLogger().addHandler(logzio_handler)
                logging.getLogger().addFilter(ExtraFieldsLogFilter({'CUSTOMER_NAME': Settings.CUSTOMER_NAME}))
        else:
            logging.error('logzio logger is not configured, while it should be')

def get_job_logger(name: str) -> logging.Logger:
    """
    Create a logger for a given name, overriding the default logger log level with LOG_LEVEL env var, if set
    """
    logger = logging.getLogger(name)

    if Settings.LOG_LEVEL:
        logger.setLevel(int(Settings.LOG_LEVEL))

    return logger

def get_prefect_logger() -> Optional[logging.Logger]:
    import prefect
    import prefect.exceptions
    try:
        logger_ = prefect.get_run_logger()
    except prefect.exceptions.MissingContextError:
        logger_ = None
    return logger_


def get_vl_logger(name: str = None) -> logging.Logger:
    global _LOGGING_INITIALIZED

    if not _LOGGING_INITIALIZED:
        _init_logging()
        _LOGGING_INITIALIZED = True

    if Settings.PREFECT_LOGGING_ENABLED:
        logger_ = get_prefect_logger()
    else:
        logger_ = None
    if not name:
        name = "vl.root"
    else:
        name = "vl.root." + name

    if not logger_:
        logger_ = logging.getLogger(name)

    return logger_

def get_timing_logger(name: str = None) -> logging.Logger:
    global _LOGGING_INITIALIZED

    if not _LOGGING_INITIALIZED:
        _init_logging()
        _LOGGING_INITIALIZED = True

    if Settings.PREFECT_LOGGING_ENABLED:
        logger_ = get_prefect_logger()
    else:
        logger_ = None
    if not name:
        name = "vl.timing"
    else:
        name = "vl.timing." + name

    if not logger_:
        logger_ = logging.getLogger(name)

    return logger_

def get_fastdup_logger(name: str = None) -> logging.Logger:
    global _LOGGING_INITIALIZED

    if not _LOGGING_INITIALIZED:
        _init_logging()
        _LOGGING_INITIALIZED = True
        
    if not name:
        name = "vl.fastdup"
    else:
        name = "vl.fastdup." + name

    logger_ = logging.getLogger(name)

    return logger_