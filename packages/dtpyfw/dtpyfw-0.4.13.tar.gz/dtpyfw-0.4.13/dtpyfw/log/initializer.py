import logging

from .config import LogConfig
from .handlers import get_handlers_data

__all__ = (
    "log_initializer",
    "celery_logger_handler",
)


def log_initializer(config: LogConfig):
    celery_mode = config.get("celery_mode", True)

    handlers, log_level = get_handlers_data(config=config)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    celery_logger = logging.getLogger("celery")

    if celery_mode:
        celery_logger.setLevel(log_level)

    for handle in handlers:
        root_logger.addHandler(handle)
        if celery_mode:
            celery_logger.addHandler(handle)


def celery_logger_handler(config: LogConfig, logger, propagate):
    celery_mode = config.get("celery_mode", True)
    if celery_mode:
        handlers, log_level = get_handlers_data(config=config)
        logger.logLevel = log_level
        logger.propagate = propagate
        for handle in handlers:
            logger.addHandler(handle)
    else:
        return None
