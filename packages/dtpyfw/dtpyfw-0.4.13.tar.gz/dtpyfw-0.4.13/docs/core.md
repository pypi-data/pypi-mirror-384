# Core Sub-Package

**DealerTower Python Framework** — Fundamental utilities shared across DealerTower microservices, covering environment management, error handling, async bridging, data chunking, request helpers, and general helpers.

## Overview

The `core` sub-package provides essential building blocks:

- **Environment Management**: Controlled loading and retrieval of OS variables.
- **Exception Handling**: Structured exceptions and traceback extraction.
- **Async-to-Sync Bridge**: Run async coroutines in sync contexts.
- **Data Chunking**: Split lists into fixed-size chunks or generators.
- **HTTP Request Wrapper**: Simplified REST calls with telemetry.
- **Optional Dependency Checks**: Guard against missing extras.
- **Retry Logic**: Decorators for sync/async retry with backoff.
- **File & Folder Helpers**: Directory creation and file operations.
- **Safe Accessors**: Graceful error suppression and type conversions.
- **Singleton Patterns**: Class-level and args-based singletons.
- **Slug & URL Utilities**: Slug generation and query parameter helpers.
- **Validation Helpers**: Common validators (email, VIN, UUID, URL).
- **JSONable Encoder & Hashing**: Serialize objects and generate hashes.
- **Enum Types**: Reusable enumerations.

---

## Installation

Core utilities are included in the base installation:

```bash
pip install dtpyfw
```

---

## Module Reference

### `env.py` — Environment Variables

Load, whitelist, and retrieve environment variables with caching:

```python
from dtpyfw.core.env import Env

# Register allowed keys
Env.register({'DB_HOST', 'DB_PORT'})

# Load `.env` file
Env.load_file('.env', override=False, fail_on_missing=False)

# Retrieve values
db_host = Env.get('DB_HOST', 'localhost')
```

| Method      | Signature                                                             | Description                                     |
|-------------|-----------------------------------------------------------------------|-------------------------------------------------|
| `load_file` | `(file_path: str, override: bool=False, fail_on_missing: bool=False)` | Parse `KEY=VALUE` lines, set only allowed keys. |
| `register`  | `(variables: list\|set)`                                              | Whitelist variable names (case-insensitive).    |
| `get`       | `(key: str, default: Any=None) -> Any`                                | LRU-cached access to `os.environ`.              |

---

### `exception.py` — Error Handling

Define custom exceptions and extract traceback details:

```python
from dtpyfw.core.exception import RequestException, exception_to_dict

# Raise in your code
raise RequestException(404, 'UserController', 'User not found')

# Convert exception to dict
try: ...
except Exception as e:
    info = exception_to_dict(e)
```

**Classes & Functions:**

- `RequestException(status_code: int=500, controller: str=None, message: str='', skip_footprint: bool=False)`
- `exception_to_dict(exc) -> dict` — `{type, message, args, traceback: [...]}`

---

### `async.py` — Async Bridge

Run async coroutines in sync contexts:

```python
from dtpyfw.core.async import async_to_sync

result = async_to_sync(async_func(...))
```

- `async_to_sync(awaitable)` — Executes an awaitable on the running loop.

---

### `chunking.py` — Data Chunking

Split lists into chunks:

```python
from dtpyfw.core.chunking import chunk_list, chunk_list_generator

chunks = chunk_list(my_list, chunk_size=100)
for batch in chunk_list_generator(my_list, 100):
    process(batch)
```

- `chunk_list(lst, size) -> list[list]`
- `chunk_list_generator(lst, size)` — generator yielding sublists.

---

### `enums.py` — Common Enums

```python
from dtpyfw.core.enums import OrderingType

# Use in sorting logic
order = OrderingType.asc
```

- `class OrderingType(str, Enum): desc, asc`

---

### `file_folder.py` — File & Directory Helpers

```python
from dtpyfw.core.file_folder import make_directory, folder_path_of_file, remove_file

make_directory('/tmp/data')
path = folder_path_of_file(__file__)
remove_file('/tmp/data/old.txt')
```

---

### `jsonable_encoder.py` — JSON Encoder

Serialize complex data safely:

```python
from dtpyfw.core.jsonable_encoder import jsonable_encoder

data = jsonable_encoder(my_object)
```

- Converts objects to JSON-compatible dict via `json.dumps(..., default=str)`.
### `hashing.py` — Generic Hashing

Hash arbitrary data to stable hex digests:

```python
from dtpyfw.core.hashing import hash_data

digest = hash_data({"foo": 123}, algorithm="sha256")
```

Supports `md5`, `sha1`, `sha256`, `sha512`, `blake2b`, and `blake2s`.

### `require_extra.py` — Optional Dependency Checks

Ensure optional modules are installed before using features that rely on them:

```python
from dtpyfw.core.require_extra import require_extra

require_extra("redis", "redis")
```

- `require_extra(extra_name, *modules)` raises `RuntimeError` if any module is missing.




---

### `request.py` — HTTP Requests

Wrapper over `requests` with logging:

```python
from dtpyfw.core.request import request

resp = request(
    method='GET',
    path='/api/data',
    host='https://api.example.com',
    auth_key='X-API-KEY',
    auth_value='token',
    disable_caching=True
)
```

- Handles JSON parsing, error telemetry (`footprint`), and raises `RequestException`. Key options include `auth_type` ("headers" or "params"), `internal_service` response handling, toggling JSON parsing with `json_return`, or returning the raw response via `full_return`.

---

### `retry.py` — Retry Decorators

Retry sync/async functions with backoff:

```python
from dtpyfw.core.retry import retry

@retry(max_attempts=5, sleep_time=1, backoff=2)
def unstable():
    ...

@retry(sleep_time=1)
async def unstable_async():
    ...
```

---

### `safe_access.py` — Safe Accessors

Suppress errors or convert types:

```python
from dtpyfw.core.safe_access import safe_access, convert_to_int_or_float

value = safe_access(lambda: risky_call(), default_value=None)
num = convert_to_int_or_float('123.0')  # int 123
```

---

### `singleton.py` — Singleton Patterns

Create singletons by class or by args:

```python
from dtpyfw.core.singleton import singleton_class, singleton_class_by_args

@singleton_class
class Config: ...

@singleton_class_by_args
class Cache: ...
```

---

### `slug.py` — Slug Generation

```python
from dtpyfw.core.slug import create_slug

slug = create_slug("Hello World!")  # "hello-world"
```

---

### `url.py` — URL Utilities

Add query parameters to URLs:

```python
from dtpyfw.core.url import add_query_param

new_url = add_query_param('https://example.com', {'page': 2, 'q': 'hi'})
```

---

### `validation.py` — Validators

Common validators:

```python
from dtpyfw.core.validation import is_email, is_vin, is_year, is_uuid, is_valid_http_url

assert is_email('test@example.com')
assert is_vin('1HGCM82633A004352')
```

---

*This documentation covers the `core` sub-package of the DealerTower Python Framework.*
