"""Celery worker helpers: task registration and worker configuration."""

from ..core.require_extra import require_extra

__all__ = (
    "limited",
    "task",
    "worker",
)

require_extra("worker", "redis", "celery")
