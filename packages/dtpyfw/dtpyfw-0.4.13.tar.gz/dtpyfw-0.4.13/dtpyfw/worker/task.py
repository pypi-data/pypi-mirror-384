"""Task registry utilities for Celery routing and scheduling."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Sequence, Tuple

from celery.schedules import crontab

__all__ = ("Task",)


class Task:
    """Collect and expose Celery tasks, routes, and periodic schedules."""

    _tasks: List[str] = []
    _tasks_routes: Dict = {}
    _periodic_tasks: Dict = {}

    def _register_task_route(self, route: str) -> "Task":
        """Register a task route for autodiscovery."""
        self._tasks.append(route)
        return self

    def register(self, route: str, queue: str | None = None) -> "Task":
        """Register a single task and optional queue routing."""
        self._register_task_route(route=route)
        task_dict = {}
        if queue:
            task_dict["queue"] = queue

        self._tasks_routes[route] = task_dict
        return self

    def bulk_register(self, routes: Sequence[str], queue: str | None = None) -> "Task":
        """Register multiple tasks with an optional shared queue."""
        for route in routes:
            self.register(route=route, queue=queue)
        return self

    def register_periodic_task(
        self,
        route: str,
        schedule: crontab | timedelta,
        queue: str | None = None,
        *args: Any,
    ) -> "Task":
        """Register a periodic task with schedule and optional args."""
        self.register(route=route, queue=queue)
        self._periodic_tasks[route] = {
            "task": route,
            "schedule": schedule,
            "args": args,
        }
        return self

    def bulk_register_periodic_task(
        self,
        tasks: Sequence[Tuple[str, crontab | timedelta, Sequence]],
        queue: str | None = None,
    ) -> "Task":
        """Register a batch of periodic tasks, optionally with a queue."""
        for route, schedule, args in tasks:
            self.register_periodic_task(
                route=route, schedule=schedule, queue=queue, *args
            )
        return self

    def get_tasks(self) -> list[str]:
        """Return the list of registered task module paths."""
        return self._tasks

    def get_tasks_routes(self) -> dict:
        """Return the routing map for registered tasks."""
        return self._tasks_routes

    def get_periodic_tasks(self) -> dict:
        """Return the configured periodic tasks schedule mapping."""
        return self._periodic_tasks
