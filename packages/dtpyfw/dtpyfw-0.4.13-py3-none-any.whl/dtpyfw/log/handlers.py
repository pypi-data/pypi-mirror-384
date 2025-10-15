import logging
from logging.handlers import RotatingFileHandler

from .api_handler import LoggerHandler
from .config import LogConfig
from .formatter import CustomFormatter

__all__ = ("get_handlers_data",)


def get_handlers_data(config: LogConfig):
    formatter = CustomFormatter()

    logging_api_url = config.get("api_url")
    logging_api_key = config.get("api_key")
    only_footprint_mode = config.get("only_footprint_mode", True)

    log_print = config.get("log_print", default=False)
    log_store = config.get("log_store", default=False)
    log_level = getattr(logging, config.get("log_level", default="INFO"))

    handlers = []

    if logging_api_url and logging_api_key:
        api_handler = LoggerHandler(
            logging_api_url=logging_api_url,
            logging_api_key=logging_api_key,
            only_footprint_mode=only_footprint_mode,
        )
        api_handler.setLevel(log_level)
        api_handler.setFormatter(formatter)
        handlers.append(api_handler)

    if log_print:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    if log_store:
        log_file_name = config.get("log_file_name")
        log_file_backup_count = config.get("log_file_backup_count")
        log_file_max_size = config.get("log_file_max_size")
        rotating_handler = RotatingFileHandler(
            log_file_name, maxBytes=log_file_max_size, backupCount=log_file_backup_count
        )
        rotating_handler.setLevel(log_level)
        rotating_handler.setFormatter(formatter)
        handlers.append(rotating_handler)

    return handlers, log_level
