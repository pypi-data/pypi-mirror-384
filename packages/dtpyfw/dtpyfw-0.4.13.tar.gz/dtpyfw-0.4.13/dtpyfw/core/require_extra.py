"""Utility to assert optional dependencies are installed."""

from importlib.util import find_spec

__all__ = ("require_extra",)


def require_extra(extra_name: str, *modules: str) -> None:
    """Raise ``RuntimeError`` if any of ``modules`` cannot be imported."""

    for mod in modules:
        if find_spec(mod) is None:
            raise RuntimeError(
                f"Missing optional dependency `{mod}`. "
                f"Install with `pip install dtpyfw[{extra_name}]`."
            )
