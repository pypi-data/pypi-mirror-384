# Redis Sub-Package

**DealerTower Python Framework** — Unified Redis and Redis Streams utilities to standardize caching, message consumption, and connection management across microservices.

## Overview

The `redis` sub-package provides:

- **Connection Management** with synchronous and asynchronous clients via a fluent `RedisConfig` and `RedisInstance`.
- **Caching Decorator** (`cache_function`) and decorator helper (`cache_wrapper`) to transparently cache function results with namespaces and expiration.
- **Sender Class** (`Sender`) for publishing JSON messages to Redis Streams.
- **Consumer Class** (`Consumer`) for robust Redis Streams consumption with retry logic, handler registration, and message acknowledgment tracking.
- **Health Check** (`is_redis_connected`) to verify Redis availability.

This centralizes Redis interactions, reducing boilerplate and ensuring consistent patterns.

## Installation

Install the `redis` extra to include necessary dependencies:

```bash
pip install dtpyfw[redis]
```

## Configuration

### RedisConfig

Fluent interface to set up Redis connection parameters:

| Method                       | Description                                |
|------------------------------|--------------------------------------------|
| `set_redis_url(url: str)`    | Full Redis DSN (overrides host/port/db).   |
| `set_redis_host(host: str)`  | Redis host (e.g., `localhost`).            |
| `set_redis_port(port: int)`  | Redis port (e.g., `6379`).                 |
| `set_redis_db(db: str)`      | Database index or name (default `0`).      |
| `set_redis_username(user)`   | Username, if required.                     |
| `set_redis_password(pwd)`    | Password for AUTH.                         |
| `set_redis_ssl(ssl: bool)`   | Use TLS (`True`) or plain TCP (`False`).   |
| `get(key, default=None)`     | Retrieve a config value.                   |

```python
from dtpyfw.redis.config import RedisConfig

config = (
    RedisConfig()
    .set_redis_host("localhost")
    .set_redis_port(6379)
    .set_redis_db("0")
    .set_redis_password("secret")
    .set_redis_ssl(False)
)
```

## Connection Management

### RedisInstance

Creates sync and async Redis clients:

```python
from dtpyfw.redis.connection import RedisInstance

redis_instance = RedisInstance(config)
```

**Attributes:**

- `redis_instance.redis_url` — Final DSN string.

**Context Managers:**

- `get_redis()` — yields `redis.Redis`, closes on exit.
- `get_async_redis()` — async context for `redis.asyncio.Redis`.

**Direct Clients:**

- `get_redis_client()` — returns `redis.Redis`.
- `get_async_redis_client()` — returns `AsyncRedis`.
- `get_redis_url()` — return the computed Redis connection URL.

```python
# Synchronous
with redis_instance.get_redis() as client:
    client.set("key", "value")

# Asynchronous
async with redis_instance.get_async_redis() as async_client:
    await async_client.get("key")
```

## Caching Utilities

### `cache_function`

Decorator to cache function results in Redis:

```python
from dtpyfw.redis.caching import cache_function, cache_wrapper

@cache_function(
    func=my_func,
    redis=redis_instance,
    namespace="my_namespace",
    expire=3600,
    cache_only_for=[{"kwarg": "state", "operator": "in", "value": ["used"]}],
    skip_cache_keys={"db"}
)
def my_func(param1, state, db=None):
    # expensive operation
    return result

# Alternatively use as a decorator
@cache_wrapper(
    redis=redis_instance,
    namespace="my_namespace",
    expire=3600,
)
def my_other_func(x):
    ...
```

Parameters:

- `func` — target callable.
- `redis` — `RedisInstance`.
- `namespace` — prefix for keys.
- `expire` — TTL in seconds.
- `cache_only_for` — list of dicts to conditionally cache.
- `skip_cache_keys` — set of kwargs to exclude from key.

## Sender (Redis Streams)

### `Sender`

Publish JSON-encoded messages to Redis Streams.

```python
from dtpyfw.redis.sender import Sender, Message

sender = Sender(redis_instance)
sender.register_channel("orders")

msg = Message(name="order.created", body={"id": 1})
sender.send_message("orders", msg)
```

Key Methods:

- `register_channel(channel_name)` — track a stream for publishing.
- `send_message(channel, message)` — add a message to the stream.

## Consumer (Redis Streams)

### `Consumer`

High-level Redis Streams consumer with auto group creation, retries, and cleanup:

```python
from dtpyfw.redis.streamer import Consumer

consumer = Consumer(redis_instance, consumer_name="worker1")

# Register channel and handler
consumer.register_channel(
    "orders",
    consumers=["worker1"],
    message_cleanup=True,
    read_messages=True,
)
consumer.register_handler("orders", handler_func)

# Continuously consume from all channels
consumer.persist_consume_all_channels(rest_time=5, block_time=1)

# Periodically remove fully acknowledged messages
consumer.clean_up_consumed_messages()
```

Key Methods:

- `register_channel(channel_name, read_messages, consumers, message_cleanup)`
- `register_handler(channel, func)`
- `consume_messages(channel, consumer_group, block_time)` — process a single message batch.
- `persist_consume_messages(channel, consumer_group, rest_time, block_time)` — loop consumption for one channel.
- `consume_all_channels(block_time)` — read messages from all registered channels.
- `persist_consume_all_channels(rest_time, block_time)` — loop consumption for all channels.
- `clean_up_consumed_messages()` — delete fully acknowledged entries.

## Health Check

### `is_redis_connected`

```python
from dtpyfw.redis.health import is_redis_connected

healthy, error = is_redis_connected(redis_instance)
```

Returns `(True, None)` if reachable or `(False, Exception)` on failure.

---

*This documentation covers the `redis` sub-package of the DealerTower Python Framework. Ensure the `redis` extra is installed to use these features.*
