"""FastAPI helpers: application wrapper, middlewares, routes, and schemas."""

from ..core.require_extra import require_extra

__all__ = (
    "application",
    "middlewares",
    "routes",
    "schemas",
)

require_extra("api", "fastapi", "starlette", "pydantic")
