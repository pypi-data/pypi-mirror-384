"""Wrapper around :func:`json.dumps` that forces serialisation of unknown
types."""

import json
from typing import Any

__all__ = ("jsonable_encoder",)


def jsonable_encoder(data: Any) -> Any:
    """Return ``data`` encoded to JSON and back to ensure primitives only."""

    return json.loads(json.dumps(data, default=str))
