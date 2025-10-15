# Worker Sub-Package

**DealerTower Python Framework** — Simplifies Celery task and worker configuration by providing `Task` and `Worker` helper classes for registering tasks, scheduling jobs and building a Celery application with minimal boilerplate.

## Overview

The `worker` sub‑package centralizes Celery setup across microservices. It offers:

- **Task registration** via the `Task` class to declare task routes and periodic schedules.
- **Worker configuration** through the `Worker` class using fluent setters for broker, serializers, timezone and other options.
- **Automatic task discovery** and schedule registration using Redis and Celery RedBeat.
- **Secure Redis broker/backend** integration with SSL support.

## Installation

Install the `worker` extra to include the required dependencies:

```bash
pip install dtpyfw[worker]
```

Dependencies: `celery`, `celery-redbeat`

## Task Class

### `Task`

Use `Task` to register tasks and periodic tasks:

```python
from celery.schedules import crontab
from dtpyfw.worker.task import Task

tasks = (
    Task()
    .register("my_app.tasks.process")
    .register_periodic_task(
        "my_app.tasks.cleanup",
        schedule=crontab(hour=0, minute=0),
    )
)
```

**Methods**

| Method | Description |
|------------------------------|------------------------------------------------------------------|
| `register(route: str, queue: str | None = None)` | Register a task import path and optional queue. |
| `bulk_register(routes: Sequence[str], queue: str | None = None)` | Register multiple task routes at once. |
| `register_periodic_task(route: str, schedule: crontab | timedelta, queue: str | None = None, *args)` | Schedule a periodic task using crontab or `timedelta`. |
| `bulk_register_periodic_task(tasks: Sequence[Tuple[str, crontab | timedelta, Sequence]], queue: str | None = None)` | Register multiple periodic tasks. |
| `get_tasks() -> list[str]` | List of registered task routes. |
| `get_tasks_routes() -> dict` | Mapping for Celery `task_routes`. |
| `get_periodic_tasks() -> dict` | Mapping for Celery `beat_schedule`. |

## Worker Class

### `Worker`

`Worker` assembles a Celery application from the registered tasks and a configured Redis instance:

```python
from celery.schedules import crontab
from dtpyfw.worker.task import Task
from dtpyfw.worker.worker import Worker
from dtpyfw.redis.connection import RedisInstance, RedisConfig

redis_cfg = (
    RedisConfig()
    .set_redis_host("localhost")
    .set_redis_port(6379)
    .set_redis_db(0)
)
redis = RedisInstance(redis_cfg)

tasks = Task().register("my_app.tasks.process")
worker = (
    Worker()
    .set_task(tasks)
    .set_redis(redis)
    .set_name("dealer_celery_app")
    .set_timezone("UTC")
    .set_task_serializer("json")
    .set_result_serializer("json")
    .set_enable_utc(True)
)

celery_app = worker.create()
```

**Fluent setters**

| Method | Description |
|-------------------------------------------------------|-------------------------------------------------------------|
| `set_task(task: Task)`                                | Register tasks and periodic schedules. |
| `set_redis(redis_instance: RedisInstance)`            | Configure Redis broker/backend URL and SSL if needed. |
| `set_name(name: str)`                                 | Set the Celery application name. |
| `set_timezone(timezone: str)`                         | Define the timezone for the scheduler. |
| `set_task_serializer(serializer: str)`                | Task message serializer (e.g. `"json"`). |
| `set_result_serializer(serializer: str)`              | Result serializer. |
| `set_track_started(value: bool)`                      | Enable `task_track_started`. |
| `set_result_persistent(value: bool)`                  | Make result backend persistent. |
| `set_worker_prefetch_multiplier(number: int)`         | Prefetch multiplier for worker processes. |
| `set_broker_prefix(prefix: str)`                      | Prefix for broker keys in Redis. |
| `set_backend_prefix(prefix: str)`                     | Prefix for result backend keys in Redis. |
| `set_redbeat_key_prefix(prefix: str)`                 | Prefix for RedBeat scheduler keys. |
| `set_redbeat_lock_key(key: str)`                      | Lock key used by RedBeat scheduler. |
| `set_enable_utc(value: bool)`                         | Enable or disable UTC support. |
| `set_broker_connection_max_retries(value: int)`       | Maximum broker connection retries. |
| `set_broker_connection_retry_on_startup(value: bool)` | Retry broker connection on startup. |
| `set_result_expires(seconds: int)`                    | Expiration time for task results. |
| `set_limited_tasks_prefix(prefix: str)`               | Prefix for limited/unique task keys. |
| `set_limited_tasks_default_ttl(ttl: int)`             | Default TTL for limited tasks. |
| `set_limited_tasks_default_queue_limit(limit: int)`   | Default queue limit for limited tasks. |
| `set_limited_tasks_default_concurrency(value: int)`   | Default concurrency for limited tasks. |

`create()` returns a configured `Celery` instance with registered tasks automatically discovered.

## Creating and Running the Worker

1. Save the `celery_app` to a module (for example `celery_app = worker.create()` in `my_app/celery_app.py`).
2. **Run Worker**:
   ```bash
   celery -A my_app.celery_app worker --loglevel=info
   ```
3. **Run Scheduler (Beat)**:
   ```bash
   celery -A my_app.celery_app beat --loglevel=info
   ```

## Best Practices

- Use **namespaced task routes** to avoid collisions.
- Define **explicit queues** for different task categories.
- Monitor scheduled tasks and results regularly.
- Secure Redis with **SSL** by using `rediss://` URLs and enabling SSL flags.

