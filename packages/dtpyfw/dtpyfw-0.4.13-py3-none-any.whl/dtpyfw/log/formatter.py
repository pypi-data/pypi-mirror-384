import logging

__all__ = ("CustomFormatter",)


class CustomFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(None, "%Y-%m-%d %H:%M:%S")

    def format(self, record):
        if hasattr(record, "details"):
            self._style._fmt = "%(asctime)s - %(levelname)s - %(details)s"
        else:
            self._style._fmt = "%(asctime)s - %(levelname)s - %(message)s"
        return super().format(record)
