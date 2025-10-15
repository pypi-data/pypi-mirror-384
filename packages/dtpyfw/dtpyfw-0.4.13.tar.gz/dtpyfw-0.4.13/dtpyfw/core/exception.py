"""Custom exceptions and helpers for serializing them."""

"""Exception helpers used across the dtpyfw package."""

import sys
import traceback

__all__ = (
    "RequestException",
    "exception_to_dict",
)


class RequestException(Exception):
    """Exception raised when a handled HTTP request fails."""

    def __init__(
        self,
        status_code: int = 500,
        controller: str | None = None,
        message: str = "",
        skip_footprint: bool = True,
    ) -> None:
        self.status_code = status_code
        self.controller = controller
        self.message = message
        self.skip_footprint = skip_footprint
        super().__init__(self.controller)


def exception_to_dict(exc: Exception) -> dict:
    """Return a serialisable dictionary representing ``exc``."""

    exc_type, exc_obj, tb = sys.exc_info()

    exc_dict = {
        "type": str(exc_type.__name__),
        "message": str(exc),
    }

    tb_info = traceback.extract_tb(tb)
    detailed_tb = []
    for tb in tb_info:
        tb_details = {
            "filename": tb.filename,
            "line": tb.lineno,
            "function": tb.name,
            "text": tb.line,
        }
        detailed_tb.append(tb_details)

    exc_dict["traceback"] = detailed_tb

    if hasattr(exc, "args"):
        exc_dict["args"] = exc.args

    return exc_dict
