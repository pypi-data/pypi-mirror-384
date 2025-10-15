# Log Sub-Package

**DealerTower Python Framework** — Structured logging utilities with optional remote API delivery, console/file output, and Celery integration.

## Overview

The `log` sub-package provides:

- **LogConfig** builder to define API endpoint, credentials, output options, and other settings.
- **log_initializer** function to initialize the root logger with API, console, and rotating file handlers.
- **celery_logger_handler** helper to attach the same handlers to arbitrary Celery loggers.
- **footprint.leave** convenience function to create structured log entries.
- **CustomFormatter** ensures a consistent timestamped format and supports custom `details`.
- **LoggerHandler** posts logs to an HTTP endpoint with automatic retry.

This centralizes logging setup across microservices.

## Configuration

Create a `LogConfig` instance and set the desired options:

```python
from dtpyfw.log import LogConfig

cfg = (
    LogConfig()
    .set_api_url("https://log.example.com")    # remote endpoint
    .set_api_key("TOKEN")                      # API credential
    .set_log_level("INFO")                     # logging level
    .set_log_print(True)                       # enable console output
    .set_log_store(True)                       # persist logs to file
    .set_log_file_name("app.log")              # file path
    .set_log_file_max_size(5_000_000)          # rotate when size exceeded
    .set_log_file_backup_count(10)             # number of rotations
    .set_only_footprint_mode(False)            # send any log record
    .set_celery_mode(True)                     # also configure Celery loggers
)
```

Any option can be omitted; defaults disable API logging, file storage, and Celery support.

## Initialization

Pass the configuration to `log_initializer` to set up handlers on the root logger:

```python
from dtpyfw.log import log_initializer

log_initializer(cfg)
```

For Celery workers created outside of this initialization, use `celery_logger_handler(cfg, logger, propagate)` to attach handlers manually.

## Footprint Telemetry

Use `footprint.leave` to emit a structured entry. All keyword arguments are placed in the `details` field:

```python
from dtpyfw.log import footprint

footprint.leave(
    log_type="warning",
    subject="Payment Failed",
    controller="order",
    message="Credit card declined",
    payload={"order_id": 123},
)
```

When `only_footprint_mode` is enabled, only records emitted via `footprint.leave` will be sent to the API handler.

---

*This documentation covers the `log` sub-package of the DealerTower Python Framework.*
