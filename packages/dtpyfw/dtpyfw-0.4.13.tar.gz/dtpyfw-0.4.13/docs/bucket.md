# Bucket Sub-Package

**DealerTower Python Framework** — Simplified S3-compatible storage operations through the `Bucket` class which wraps `boto3`.
It reduces boilerplate and standardizes file management across microservices.

## Overview

The `bucket` sub-package exposes an easy interface for working with AWS S3 or any S3-compatible service. It features:

- Automatic client configuration with credentials, endpoint URLs and region settings.
- URL generation for stored objects.
- Common file operations: upload, download, duplicate, safe duplicate and delete.
- Support for uploading raw bytes or files from disk.
- Consistent error handling via `RequestException` from `dtpyfw.core.exception`.

## Installation

Install with the `bucket` extra to pull in `boto3` and `botocore`:

```bash
pip install dtpyfw[bucket]
```

## Bucket Class

### Initialization

```python
from dtpyfw.bucket.bucket import Bucket

bucket = Bucket(
    name="my-bucket",
    s3_mode=False,                     # True for AWS S3
    endpoint_url="https://s3.example.com",  # Base URL for object access
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
    region_name="us-east-1",
)
```

| Parameter      | Type  | Description |
|---------------|-------|-------------|
| `name`        | `str` | Bucket name used for all API calls. |
| `s3_mode`     | `bool`| Set `True` for AWS S3 (`region_name` required). When `False`, `endpoint_url` is used for a compatible service. |
| `endpoint_url`| `str` | Base URL for generating object URLs. Ignored by the boto3 client when `s3_mode=True`. |
| `access_key`  | `str` | Access key ID. |
| `secret_key`  | `str` | Secret access key. |
| `region_name` | `str` | AWS region when using S3 mode. |

### Methods

#### `url_generator(key: str) -> str`

Return the public URL for an object key.

```python
url = bucket.url_generator("path/to/object.png")
```

#### `get_s3() -> BaseClient`

Retrieve the underlying `boto3` S3 client for custom calls.

```python
s3_client = bucket.get_s3()
```

#### `get_bucket_name() -> Optional[str]`

Return the configured bucket name.

```python
name = bucket.get_bucket_name()
```

#### `check_file_exists(key: str) -> bool`

Check whether an object exists.

```python
exists = bucket.check_file_exists("README.md")
```

#### `upload(file: bytes, key: str, content_type: str, cache_control: str = 'no-cache') -> str`

Upload a bytes object and return its URL.

```python
with open("image.png", "rb") as f:
    data = f.read()
url = bucket.upload(data, "images/image.png", content_type="image/png")
```

#### `upload_by_path(file_path: str, key: str, content_type: str | None = None, cache_control: str = 'no-cache') -> str`

Upload a local file by reading it from disk.

```python
url = bucket.upload_by_path("local/path/file.pdf", "docs/manual.pdf", content_type="application/pdf")
```

#### `download(key: str, filepath: str) -> bool`

Download an object to a local file path.

```python
bucket.download("reports/2025.csv", "/tmp/2025.csv")
```

#### `download_fileobj(key: str, file_obj) -> bool`

Download an object into a file-like object.

```python
from io import BytesIO
buffer = BytesIO()
bucket.download_fileobj("archive/backup.zip", buffer)
```

#### `duplicate(source_key: str, destination_key: str, cache_control: str = 'no-cache') -> str`

Copy an object to a new key.

```python
new_url = bucket.duplicate("images/photo.jpg", "images/photo-copy.jpg")
```

#### `safe_duplicate(source_key: str, cache_control: str = 'no-cache') -> str`

Duplicate an object with automatic renaming if the destination exists.

```python
new_url = bucket.safe_duplicate("archive/log.txt")
```

#### `delete(key: str) -> bool`

Remove an object from the bucket.

```python
bucket.delete("temp/file.tmp")
```

## Error Handling

All methods raise `RequestException` when credentials are invalid or other S3 errors occur:

```python
from dtpyfw.core.exception import RequestException

try:
    bucket.upload(b"data", "key", "text/plain")
except RequestException as e:
    print(f"Error: {e.message} (status {e.status_code})")
```
