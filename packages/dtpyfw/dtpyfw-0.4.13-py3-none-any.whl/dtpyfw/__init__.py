"""DealerTower Python Framework package metadata."""

from importlib.metadata import PackageNotFoundError, version

__all__ = (
    "api",
    "bucket",
    "core",
    "db",
    "encrypt",
    "ftp",
    "kafka",
    "log",
    "redis",
    "worker",
)

__title__ = "dtpyfw"
__description__ = (
    "DealerTower Python Framework: reusable building-blocks for DealerTower services"
)
__author__ = "Reza Shirazi"
__author_email__ = "reza@dealertower.com"
__license__ = "DealerTower Proprietary License"

try:
    __version__ = version(__title__)
except PackageNotFoundError:  # pragma: no cover - when package not installed
    __version__ = "0.0.0"
