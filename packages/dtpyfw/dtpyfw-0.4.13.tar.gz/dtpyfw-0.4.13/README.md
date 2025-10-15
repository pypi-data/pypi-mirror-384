# DealerTower Python Framework (dtpyfw)

**DealerTower Framework** provides reusable building blocks for microservices. It is organized into modular sub-packages focused on different domains: Core, API, Database, Bucket, FTP, Redis, Kafka, Worker, Log, and Encryption.

---

## 🚀 Installation

Requires **Python 3.11** or newer.

### Base package & Core

```bash
pip install dtpyfw
```

Using Poetry (development):

```bash
poetry install -E all
```

### Package Metadata

Query the installed version programmatically:

```python
import dtpyfw
print(dtpyfw.__version__)
```

### Optional Extras

Install just the features you need; extras can be combined, for example `pip install dtpyfw[api,db]`.

| Sub-Package | Description | Install Command | Docs |
| ----------- | ----------- | --------------- | ---- |
| **core**    | Env, errors, async bridge, utils | included in base | [Core Docs](docs/core.md) |
| **api**     | FastAPI middleware & routing helpers | `pip install dtpyfw[api]` | [API Docs](docs/api.md) |
| **db**      | SQLAlchemy sync/async & search tools | `pip install dtpyfw[db]` | [DB Docs](docs/db.md) |
| **bucket**  | S3-compatible file management | `pip install dtpyfw[bucket]` | [Bucket Docs](docs/bucket.md) |
| **ftp**     | FTP and SFTP convenience wrappers | `pip install dtpyfw[ftp]` | [FTP Docs](docs/ftp.md) |
| **redis**   | Redis clients & Streams consumer | `pip install dtpyfw[redis]` | [Redis Docs](docs/redis.md) |
| **kafka**   | Kafka messaging utilities | `pip install dtpyfw[kafka]` | [Kafka Docs](docs/kafka.md) |
| **worker**  | Celery task & scheduler setup | `pip install dtpyfw[worker]` | [Worker Docs](docs/worker.md) |
| **log**     | Structured logging helpers | included in base | [Log Docs](docs/log.md) |
| **encrypt** | Password hashing & JWT utilities | `pip install dtpyfw[encrypt]` | [Encryption Docs](docs/encrypt.md) |
| **slim-task** | DB, Redis, Worker | `pip install dtpyfw[slim-task]` | — |
| **slim-api**  | API, DB | `pip install dtpyfw[slim-api]` | — |
| **normal**    | API, DB, Redis, Worker | `pip install dtpyfw[normal]` | — |
| **all**       | Everything above | `pip install dtpyfw[all]` | — |

---

## 📦 Sub-Package Summaries

### Core

Essential utilities for environment management, error handling, async bridging and general helpers. [Core Docs](docs/core.md)

### API

FastAPI application factory, middleware and routing helpers. [API Docs](docs/api.md)

### Database

Sync and async SQLAlchemy orchestration with search helpers. [DB Docs](docs/db.md)

### Bucket

S3-compatible storage convenience functions. [Bucket Docs](docs/bucket.md)

### FTP/SFTP

Unified clients for FTP and SFTP operations. [FTP Docs](docs/ftp.md)

### Redis & Streams

Redis caching utilities and Streams consumers/senders. [Redis Docs](docs/redis.md)

### Kafka

Producer and consumer wrappers for Kafka messaging. [Kafka Docs](docs/kafka.md)

### Worker

Helpers for configuring Celery workers and schedules. [Worker Docs](docs/worker.md)

### Log

Structured logging configuration and helpers. [Log Docs](docs/log.md)

### Encryption

Password hashing and JWT helpers. [Encryption Docs](docs/encrypt.md)

---

## 📄 License

DealerTower Python Framework is proprietary. See [LICENSE](LICENSE) for terms.

## Development

- Install dependencies: `poetry install -E all`
- Run tests: `pytest` (from repo root)
- Format and lint: `autoflake -r --remove-all-unused-imports --ignore-init-module-imports . && isort . && black . && ruff check . --fix && docformatter -r -i .`
- Type-check: `mypy dtpyfw`
