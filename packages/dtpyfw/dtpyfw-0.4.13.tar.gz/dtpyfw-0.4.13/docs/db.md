# Database (DB) Sub-Package

**DealerTower Python Framework** — Centralized SQLAlchemy configuration, connection management, ORM utilities, health checks and search helpers to streamline database interactions across microservices.

## Overview

The `db` sub-package encapsulates common patterns for working with relational databases using SQLAlchemy. It provides:

- **Configuration** via a fluent `DatabaseConfig` class.
- **Connection Management** with `DatabaseInstance` for synchronous and asynchronous sessions.
- **Model Base** (`ModelBase`) providing UUID primary keys, timestamp fields and settings helpers.
- **Health Checks** to verify connectivity.
- **Search Helpers** for dynamic filter generation and query building.
- **Upsert Utilities** for bulk inserts or updates.

This standardizes database setup and reduces boilerplate across services.

## Installation

Install with the `db` extra:

```bash
pip install dtpyfw[db]
```

## Configuration

### `DatabaseConfig`

Fluent builder for database connection settings:

| Method                                      | Description                                                    |
|---------------------------------------------|----------------------------------------------------------------|
| `set_db_url(db_url: str)`                   | Primary write database URL (e.g. `postgresql://...`).          |
| `set_db_url_read(db_url_read: str)`         | Read-only database URL (falls back to write URL).              |
| `set_db_user(db_user: str)`                 | Database username.                                             |
| `set_db_password(db_password: str)`         | Database password.                                             |
| `set_db_host(db_host: str)`                 | Host for write operations.                                     |
| `set_db_host_read(db_host_read: str)`       | Host for read-only operations.                                  |
| `set_db_port(db_port: int)`                 | Port number (e.g., `5432`).                                    |
| `set_db_name(db_name: str)`                 | Database name.                                                 |
| `set_db_ssl(db_ssl: bool)`                  | Enable SSL mode.                                               |
| `set_db_pool_size(db_pool_size: int)`       | Connection pool size.                                          |
| `set_db_max_overflow(db_max_overflow: int)` | Maximum overflow connections.                                  |

```python
from dtpyfw.db.config import DatabaseConfig

config = (
    DatabaseConfig()
    .set_db_user("user")
    .set_db_password("pass")
    .set_db_host("localhost")
    .set_db_host_read("replica")
    .set_db_port(5432)
    .set_db_name("mydb")
    .set_db_ssl(False)
    .set_db_pool_size(10)
    .set_db_max_overflow(5)
)
```

Retrieve values with `config.get(key: str, default=None)`.

## Database Instance

Manages engines and sessions for sync and async contexts.

```python
from dtpyfw.db.database import DatabaseInstance

db_instance = DatabaseInstance(config)
```

### Engines & URLs

- `db_instance.database_path_write`
- `db_instance.database_path_read`
- `db_instance.async_database_path_write`
- `db_instance.async_database_path_read`
- `db_instance.base` (Declarative base for models)

### Creating Tables

```python
db_instance.create_tables()
```

### Synchronous Sessions

```python
with db_instance.get_db_cm() as session:
    result = session.execute("SELECT 1")
    print(result.scalar())
```

### Asynchronous Sessions

```python
import asyncio

async def fetch():
    async with db_instance.async_get_db_cm() as session:
        result = await session.execute("SELECT 1")
        print(result.scalar())

asyncio.run(fetch())
```

### Health Check

```python
from dtpyfw.db.health import is_database_connected

healthy, error = is_database_connected(db_instance)
```

Or use:

```python
if db_instance.check_database_health():
    print("OK")
```

### Cleanup

Close all active connections when shutting down:

```python
db_instance.close_all_connections()
```

## Model Base & Utilities

### `ModelBase`

Mixin for ORM models:

- `id` (UUID primary key)
- `created_at` and `updated_at` timestamp columns
- `.get()` helper to produce a dictionary representation
- class methods `create()` and `update()` for simple CRUD operations
- utilities to track JSON field differences

```python
from dtpyfw.db.model import ModelBase
from sqlalchemy import Column, String

class User(db_instance.base, ModelBase):
    __tablename__ = "users"
    name = Column(String, nullable=False)
```

## Search Utilities

Dynamic filter and query builders for common use cases.

Example:

```python
from dtpyfw.db.search import get_list

get_list(
    current_query=payload.model_dump(),
    db=db,
    model=Feed,
    pre_conditions=[],
    options=[],
    distinct=True,
    get_function_parameters={
        'includes': {
            'id', 'template_id', 'template', 'title', 'is_sent', 'is_stopped', 'feed_updated_at'
        }
    },
    filters=[
        {
            'label': 'Search',
            'name': 'search',
            'type': 'search',
            'columns': [
                Feed.id,
                Feed.title,
            ],
            'hide_in_response': True,
        },
        {
            'label': 'Template',
            'name': 'template_id',
            'type': 'select',
            'columns': [
                Feed.template_id
            ],
            'labels': {
                x.id: x.title
                for x in db.query(Template).all()
            }
        }
    ],
)
```

## Additional Utilities

- **`db_instance.create_tables()`** – auto-generate tables from models.
- **`upsert_data()` / `upsert_data_async()`** – bulk insert or update records using PostgreSQL `ON CONFLICT`.

---

*This documentation covers the `db` sub-package of the DealerTower Python Framework.*

