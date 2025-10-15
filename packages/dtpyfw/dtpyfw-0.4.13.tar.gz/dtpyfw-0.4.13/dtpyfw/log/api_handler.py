import json
import logging
from time import sleep
from typing import Dict

import requests

from . import footprint

__all__ = ("LoggerHandler",)


class Logger:
    def __init__(self, logging_api_url: str, logging_api_key: str):
        self.api_url = logging_api_url
        self.api_key = logging_api_key

        self.headers = {
            "Authorization": f"{self.api_key}",
            "Content-Type": "application/json",
        }

    def log(self, details: Dict):
        controller = f"{__name__}.Logger.log"
        max_retries = 5
        backoff_seconds = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    url=self.api_url,
                    data=json.dumps(details, default=str),
                    headers=self.headers,
                )
                response.raise_for_status()
                return True
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    sleep(backoff_seconds)
                else:
                    footprint.leave(
                        log_type="warning",
                        controller=controller,
                        subject="Log Sending Error",
                        message=f"Failed to send log to API: {e}",
                        payload={
                            "data": details,
                        },
                    )


class LoggerHandler(logging.Handler):
    def __init__(
        self, logging_api_url: str, logging_api_key: str, only_footprint_mode: bool
    ):
        super().__init__()
        self.only_footprint_mode = only_footprint_mode
        self.logger = Logger(
            logging_api_url=logging_api_url,
            logging_api_key=logging_api_key,
        )

    def emit(self, record: logging.LogRecord):
        details = record.__dict__.get("details") or {}

        if self.only_footprint_mode and not details.get("footprint"):
            return None

        details["log_type"] = details.get("log_type") or record.levelname.lower()
        details["subject"] = details.get("subject") or "Unnamed"
        details["controller"] = details.get("controller") or record.funcName
        details["message"] = details.get("message") or self.format(record)
        self.logger.log(details=details)
