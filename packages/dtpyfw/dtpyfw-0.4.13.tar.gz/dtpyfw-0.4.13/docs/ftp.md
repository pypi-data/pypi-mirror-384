# FTP/SFTP Sub-Package

**DealerTower Python Framework** — Unified FTP/SFTP client built on `ftplib`, `paramiko` and `dateutil`.

## Overview

The `ftp` sub-package exposes `FTPClient`, a high level helper for uploading, downloading and managing files on FTP or SFTP servers. It hides protocol differences with a context-managed connection and provides consistent error handling.

## Installation

Install the optional extra to pull in dependencies:

```bash
pip install dtpyfw[ftp]
```

## FTPClient

### Initialization

```python
from dtpyfw.ftp.client import FTPClient

client = FTPClient(
    server="ftp.example.com",
    port=21,
    username="user",
    password="pass",
    timeout=20,
    is_sftp=False  # True for SFTP, False for FTP. None auto-detects by port.
)
```

| Parameter  | Type   | Description                                                                    |
|-----------|--------|--------------------------------------------------------------------------------|
| `server`   | `str`  | Hostname or IP address of the server.                                          |
| `port`     | `int`  | 21 for FTP or 22 for SFTP (or custom).                                         |
| `username` | `str`  | Login username.                                                                |
| `password` | `str`  | Login password.                                                                |
| `timeout`  | `int`  | Connection and operation timeout in seconds.                                   |
| `is_sftp`  | `bool` | Force SFTP or FTP. Defaults to SFTP when `port` is 22 if `None` is provided.   |

## Methods

### File and Directory Operations

#### `content(file_path: str) -> dict`

Return the text content and last modified time.

```python
data = client.content("remote/path/file.txt")
print(data["content"])
print(data["last_modified"])
```

#### `get_last_modified(file_path: str) -> dict`

Retrieve only the last modified timestamp.

```python
info = client.get_last_modified("remote/file.log")
print(info["last_modified"])
```

#### `get_folder_list(folder_path: str = "") -> list[str]`

List the files inside a remote directory.

```python
files = client.get_folder_list("/data")
```

#### `file_exists(file_path: str) -> bool`

Check whether a remote file exists.

```python
exists = client.file_exists("reports/2025.csv")
```

#### `create_directory(directory: str) -> bool`

Create a directory if it does not already exist.

```python
client.create_directory("/uploads/2025")
```

### File Transfers

#### `upload_file(local_path: str, file_path: str, confirm: bool = True) -> bool`

Upload a local file to the server.

```python
client.upload_file("local/data.csv", "/remote/data.csv")
```

#### `download_file(local_path: str, file_path: str, make_directory: bool = True, remove_file: bool = True) -> bool`

Download a remote file.

```python
client.download_file("downloads/report.csv", "/reports/report.csv")
```

#### `delete_file(file_path: str) -> bool`

Remove a remote file.

```python
client.delete_file("/temp/tmp.txt")
```

#### `rename_file(old_path: str, new_path: str) -> bool`

Rename or move a remote file.

```python
client.rename_file("/old/name.txt", "/new/name.txt")
```

## Error Handling

All methods may raise `RequestException` (from `dtpyfw.core.exception`) for connection or credential errors.

```python
from dtpyfw.core.exception import RequestException

try:
    client.download_file("local.txt", "remote.txt")
except RequestException as e:
    print(f"Error ({e.status_code}): {e.message}")
```

*Ensure the `ftp` extra is installed to use these features.*
