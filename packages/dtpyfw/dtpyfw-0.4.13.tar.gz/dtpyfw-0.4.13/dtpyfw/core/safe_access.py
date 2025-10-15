"""Utility helpers for safe attribute/function access."""

from typing import Any, Callable

__all__ = (
    "safe_access",
    "convert_to_int_or_float",
)


def safe_access(func: Callable, default_value: Any = None) -> Any:
    """Execute ``func`` and return ``default_value`` if it raises an error."""

    try:
        return func()
    except Exception:
        return default_value


def convert_to_int_or_float(string_num: str) -> int | float | None:
    """Convert a string to ``int`` or ``float`` if possible."""

    try:
        float_num = float(string_num)
        if float_num.is_integer():
            return int(float_num)
        else:
            return float_num
    except ValueError:
        return None
