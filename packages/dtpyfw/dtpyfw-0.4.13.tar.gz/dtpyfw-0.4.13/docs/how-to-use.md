# How To Use dtpyfw

This guide explains how developers or automation agents can leverage the **DealerTower Python Framework** (`dtpyfw`). Each sub‑package is optional and can be installed individually via extras. Example installation for all features:

```bash
pip install dtpyfw[all]
```

Below you will find short examples for the most common workflows along with summaries of helpful classes and functions.

## Core Utilities

The `core` package offers environment loading, exception handling, retry logic and various helpers.

```python
from dtpyfw.core.env import Env
from dtpyfw.core.retry import retry

Env.register({"API_URL"})
Env.load_file(".env")

@retry(max_attempts=3)
def fetch_data():
    ...
```

### Selected helpers

| Function/Class | Description |
| -------------- | ----------- |
| `Env.load_file(file_path: str, override: bool = False, fail_on_missing: bool = False)` | Load allowed environment variables from a file. |
| `Env.get(key: str, default: Any = None) -> Any` | Retrieve a value with caching. |
| `retry(max_attempts: int = 3, sleep_time: int = 0, backoff: int = 1)` | Decorator to retry sync/async callables. Returns wrapped function result. |
| `request(method: str, path: str, host: str, **kwargs) -> dict` | Simplified HTTP request wrapper returning JSON. |

See [core.md](core.md) for full reference.

## API

Build FastAPI services with standardized routing and middleware.

```python
from dtpyfw.api.application import Application
from dtpyfw.api.routes.router import Router
from dtpyfw.api.routes.route import Route, Method

router = Router(
    prefix="/items",
    routes=[
        Route("/", Method.GET, lambda: {"msg": "hello"})
    ],
)

app = Application(title="My API", routers=[router])
fastapi_app = app.get_app()
```

### Key components

- `Application` – wraps `FastAPI` configuration.
- `Router` – groups routes with optional auth and dependencies.
- `Route` – declares an endpoint handler with HTTP method and metadata.

More details are available in [api.md](api.md).

## Bucket (S3)

Interact with S3 compatible storage via the `Bucket` class.

```python
from dtpyfw.bucket.bucket import Bucket

bucket = Bucket(
    name="my-bucket",
    endpoint_url="https://s3.example.com",
    access_key="KEY",
    secret_key="SECRET",
)

url = bucket.upload(b"data", "path/to/file.txt", content_type="text/plain")
```

### Common methods

| Method | Returns | Description |
| ------ | ------- | ----------- |
| `url_generator(key: str)` | `str` | Public URL for an object. |
| `check_file_exists(key: str)` | `bool` | Whether object exists. |
| `upload(file: bytes, key: str, content_type: str, cache_control: str = 'no-cache')` | `str` | Upload bytes and return URL. |
| `download(key: str, filepath: str)` | `bool` | Save object to local file. |
| `duplicate(source_key: str, destination_key: str)` | `str` | Copy an object within the bucket. |

More functionality is documented in [bucket.md](bucket.md).

## Database

Configure SQLAlchemy and manage sessions using `DatabaseConfig` and `DatabaseInstance`.

```python
from dtpyfw.db.config import DatabaseConfig
from dtpyfw.db.database import DatabaseInstance

config = (
    DatabaseConfig()
    .set_db_user("user")
    .set_db_password("pass")
    .set_db_host("localhost")
    .set_db_port(5432)
    .set_db_name("mydb")
)

db = DatabaseInstance(config)

with db.get_db_cm() as session:
    result = session.execute("SELECT 1")
```

### Useful API

| Function | Description |
| -------- | ----------- |
| `DatabaseConfig.set_db_url(db_url: str)` | Provide full connection URL. |
| `DatabaseInstance.get_db_cm(force: str | None = None)` | Context manager yielding sync session. |
| `DatabaseInstance.async_get_db_cm(force: str | None = None)` | Async version for `AsyncSession`. |
| `check_database_health()` | Returns `True` if both read and write connections are alive. |

See [db.md](db.md) for advanced usage and model helpers.

## Encryption

Password hashing and JSON Web Token utilities live in the `encrypt` package.

```python
from datetime import timedelta
from dtpyfw.encrypt.hashing import Hash
from dtpyfw.encrypt.encryption import jwt_encrypt, jwt_decrypt

hashed = Hash.crypt("secret")
assert Hash.verify("secret", hashed)

token = jwt_encrypt(
    tokens_secret_key="key",
    encryption_algorithm="HS256",
    subject="user42",
    expiration_timedelta=timedelta(hours=1),
)
claims = jwt_decrypt("key", "HS256", token, subject="user42")
```

Functions:

- `Hash.crypt(password: str) -> str` – return bcrypt hash.
- `Hash.verify(plain_password: str, hashed_password: str) -> bool` – validate password.
- `jwt_encrypt(... ) -> str` – create signed token.
- `jwt_decrypt(... ) -> dict` – decode and verify token.

Details are described in [encrypt.md](encrypt.md).

## FTP/SFTP

Use `FTPClient` for FTP and SFTP operations.

```python
from dtpyfw.ftp.client import FTPClient

client = FTPClient(
    server="ftp.example.com",
    port=22,
    username="user",
    password="pass",
)

files = client.get_folder_list("/remote")
client.download_file("local.txt", "/remote/data.txt")
```

Selected methods:

| Method | Returns | Description |
| ------ | ------- | ----------- |
| `get_folder_list(folder_path: str = "")` | `list[str]` | List files in directory. |
| `upload_file(local_path: str, file_path: str)` | `bool` | Upload local file. |
| `download_file(local_path: str, file_path: str)` | `bool` | Download file. |
| `file_exists(file_path: str)` | `bool` | Check for existence. |

See [ftp.md](ftp.md) for more.

## Kafka Messaging

Produce and consume Kafka messages with minimal boilerplate.

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance
from dtpyfw.kafka.producer import Producer
from dtpyfw.kafka.consumer import Consumer

cfg = (
    KafkaConfig()
    .set_bootstrap_servers(["localhost:9092"])
    .set_group_id("my-group")
    .set_enable_auto_commit(False)
)

kafka = KafkaInstance(cfg)
producer = Producer(kafka)
producer.send("events", {"type": "created"})

consumer = Consumer(kafka, ["events"])
consumer.register_handler("events", lambda **m: print(m["value"]))
consumer.consume()
```

Important pieces:

- `KafkaConfig` – builder for connection parameters.
- `KafkaInstance.get_producer()` / `producer_context()` – create `KafkaProducer`.
- `KafkaInstance.get_consumer()` / `consumer_context()` – create `KafkaConsumer`.
- `Producer.send(topic: str, value: Any, key: bytes | str | None = None, timeout: int = 10)`.
- `Consumer.register_handler(topic: str, handler: Callable)` and `consume(timeout_ms: int = 1000)`.

See [kafka.md](kafka.md) for complete usage.

## Logging

Initialize structured logging and send records to a remote API.

```python
from dtpyfw.log import LogConfig, log_initializer, footprint

config = (
    LogConfig()
    .set_api_url("https://log.example.com")
    .set_api_key("TOKEN")
    .set_log_level("INFO")
)
log_initializer(config)

footprint.leave(log_type="info", subject="startup")
```

Key elements:

- `LogConfig` setters define API endpoint, file output and log level.
- `log_initializer(config: LogConfig)` – attach handlers to the root logger.
- `footprint.leave(**kwargs)` – emit a structured log entry.

More info in [log.md](log.md).

## Redis & Streams

Create Redis clients and leverage the caching utilities.

```python
from dtpyfw.redis.config import RedisConfig
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.caching import cache_wrapper

redis_cfg = (
    RedisConfig()
    .set_redis_host("localhost")
    .set_redis_port(6379)
    .set_redis_db("0")
)
redis = RedisInstance(redis_cfg)

@cache_wrapper(redis=redis, namespace="my", expire=60)
def compute(x):
    return x * 2
```

Other helpers:

| Function | Description |
| -------- | ----------- |
| `RedisInstance.get_redis()` | Sync context manager returning `redis.Redis`. |
| `RedisInstance.get_async_redis()` | Async context manager for `redis.asyncio.Redis`. |
| `Sender` / `Consumer` | Publish and consume Redis Stream messages. |
| `is_redis_connected(redis_instance)` | Tuple `(bool, Exception | None)` health check. |

See [redis.md](redis.md) for details.

## Celery Worker

Configure and run Celery using `Task` and `Worker` helpers.

```python
from dtpyfw.worker.task import Task
from dtpyfw.worker.worker import Worker
from dtpyfw.redis.connection import RedisInstance, RedisConfig

redis = RedisInstance(RedisConfig().set_redis_host("localhost"))

tasks = Task().register("my_app.tasks.process")
worker = (
    Worker()
    .set_task(tasks)
    .set_redis(redis)
)
celery_app = worker.create()
```

`Worker` exposes many fluent setters such as `set_name`, `set_timezone`, `set_result_expires`. Refer to [worker.md](worker.md) for the entire list.

---

This overview should help you quickly start building services with **dtpyfw**. Each sub‑package's documentation provides more in‑depth explanations and additional options.
