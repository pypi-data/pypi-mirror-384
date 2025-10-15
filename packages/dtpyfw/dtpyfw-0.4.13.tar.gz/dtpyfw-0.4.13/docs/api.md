# API Sub-Package

**DealerTower Python Framework** — FastAPI helpers for building lightweight microservices with consistent conventions.

## Overview

The `api` package wraps common FastAPI patterns:

- **Application Factory** via the `Application` class for configuring middleware, CORS, documentation routes and mounting sub‑applications or routers.
- **Declarative Routing** using `Route` and `Router` to define endpoints with optional authentication and automatic response formatting.
- **Authentication Utilities** integrating `APIKeyHeader` and `APIKeyQuery` with custom checkers.
- **Built‑in Middleware** for runtime logging, HTTP exception and validation handling, and optional internal user‑agent restriction.
- **Response Helpers** returning standardized JSON payloads with cache control headers.
- **Pydantic Schemas** such as `Sorting` and `SearchPayload` for common request bodies.

## Installation

```bash
pip install dtpyfw[api]
```

---

## Application

`Application` is a wrapper around `fastapi.FastAPI` that assembles middleware and sub‑apps.

```python
from dtpyfw.api.application import Application

main_app = Application(
    title="DealerTower Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    applications=[("/service", service_app)],  # mount another Application
    routers=[Router(prefix="/api", routes=[route])],
    gzip_min_size=1000,
    session_middleware_settings={"secret_key": "..."},
    only_internal_user_agent=True,
    cors_settings={"allow_origins": ["*"]},
)
app = main_app.get_app()
```

### Key Parameters

- `applications`: sequence of `(prefix, Application)` pairs to mount as sub‑apps.
- `routers`: list of `Router` objects or `(prefix, [Router])` tuples to include.
- `gzip_min_size`: enable GZip middleware when set.
- `session_middleware_settings`: options passed to `SessionMiddleware`.
- `middlewares`: additional custom middlewares.
- `only_internal_user_agent`: if `True`, enforces the `InternalUserAgentRestriction` middleware.
- `cors_settings`: merged with defaults (`allow_origins`, `allow_methods`, `allow_headers`, `max_age`, etc.).

`get_app()` returns the configured `FastAPI` instance.

---

## Middleware

### Runtime (`api.middlewares.runtime.Runtime`)
Captures each request, logs unhandled exceptions via `dtpyfw.log.footprint`, and returns a structured JSON error message.

### HTTP Exception Handler (`api.middlewares.http_exception`)
Formats `HTTPException` into a JSON response containing the status code and detail.

### Validation Exception Handler (`api.middlewares.validation_exception`)
Converts `RequestValidationError` into a single readable error string.

### Internal User‑Agent Restriction (`api.middlewares.user_agent.InternalUserAgentRestriction`)
Optional middleware that raises `RequestException(403)` when the `User-Agent` header is not `DealerTower-Service/1.0`.

---

## Routing and Authentication

### `AuthType` & `Auth`
`AuthType` enumerates `HEADER` and `QUERY`. The `Auth` dataclass defines the expected header/query key and value.

### `auth_data_class_to_dependency`
Converts an `Auth` instance into a list of FastAPI dependencies that combine the custom checker with `APIKeyHeader` or `APIKeyQuery`.

### Route
`Route` describes a single endpoint and can wrap its handler to emit a standard response.

```python
from dtpyfw.api.routes.route import Route, RouteMethod
from dtpyfw.api.routes.authentication import Auth, AuthType

async def handler():
    return {"msg": "ok"}

route = Route(
    path="/items",
    method=RouteMethod.GET,
    handler=handler,
    response_model=ItemModel,
    status_code=200,
    authentications=[Auth(auth_type=AuthType.HEADER, header_key="X-API-KEY", real_value="secret")],
    tags=["Items"],
    summary="List items",
    response_headers={200: {"X-Custom": "value"}},
)
```

- Works with sync or async handlers.
- Parameters control response model, dependencies, caching headers, and more.
- `errors={404: "Not found"}` builds automatic `FailedResponse` models for those status codes.

### Router
`Router` groups multiple `Route` objects under a common prefix.

```python
from dtpyfw.api.routes.router import Router

router = Router(
    prefix="/items",
    routes=[route],
    tags=["Items"],
    default_response_class=JSONResponse,
)
```

You can also supply `authentications`, additional dependencies, default responses, and control inclusion in the OpenAPI schema.

---

## Response Utilities

- `return_response(data, status_code, response_class=JSONResponse, ...)` wraps the payload in `{"success": bool, ...}` and applies no‑cache headers by default.
- `return_json_response` is a convenience wrapper that always returns `JSONResponse`.

---

## Schemas

The package ships with reusable Pydantic models:

```python
from dtpyfw.api.schemas.models import (
    Sorting, SearchPayload, NumberRange, TimeRange, DateRange, BaseModelEnumValue
)
```

`SearchPayload` validates paging (`page >= 1`, `items_per_page <= 30`) and accepts a list of `Sorting` rules. `NumberRange`, `TimeRange`, and `DateRange` represent optional min/max pairs.

### Response Schemas

``SuccessResponse[T]`` wraps successful payloads inside ``{"success": True, "data": ...}`` while ``FailedResponse`` provides ``{"success": False, "message": ...}``. Both extend ``ResponseBase`` which only defines the ``success`` field.

Example:

```python
from enum import Enum
from uuid import UUID

class FeedSearchSortBy(str, Enum):
    title = "title"

class FeedSorting(Sorting):
    sort_by: FeedSearchSortBy = FeedSearchSortBy.title

class FeedPayload(SearchPayload):
    sorting: list[FeedSorting] = [FeedSorting()]
    template_id: list[UUID] = []
    is_sent: list[bool] = []
    feed_updated_at: TimeRange | None = None
```

---
