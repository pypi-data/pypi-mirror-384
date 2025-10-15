import os

"""Utility helpers for interacting with environment variables."""

from functools import lru_cache
from typing import Any, List, Set

from ..log import footprint

__all__ = ("Env",)


class Env:
    """Lightweight wrapper around ``os.environ`` with allow-list support."""

    _allowed_variables: Set[str] = set()

    @staticmethod
    def load_file(
        file_path: str, override: bool = False, fail_on_missing: bool = False
    ) -> None:
        """Load key/value pairs from a ``.env`` style file.

        Parameters
        ----------
        file_path:
            Path to the file containing environment variables.
        override:
            When ``True`` existing environment variables will be overwritten.
        fail_on_missing:
            If ``True`` a :class:`FileNotFoundError` is raised when the file is
            missing; otherwise the call is silently ignored.
        """

        controller = f"{__name__}.Env.load_file"
        if not os.path.exists(file_path):
            if fail_on_missing:
                raise FileNotFoundError(f"The file {file_path} does not exist.")

            return

        with open(file_path, "r") as file:
            for line in file:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    key = key.strip().upper()
                    value = value.strip()
                    if key in Env._allowed_variables:
                        if override or key not in os.environ:
                            os.environ[key] = value
                    else:
                        footprint.leave(
                            log_type="warning",
                            message=f"Skipping unallowed environment variable {key}.",
                            controller=controller,
                            subject="Unallowed Environment Variable",
                        )

    @staticmethod
    def register(variables: List[str] | Set[str]) -> None:
        """Register environment variable names that are allowed to be
        loaded."""
        Env._allowed_variables.update([item.upper() for item in variables])

    @staticmethod
    @lru_cache(maxsize=128)
    def get(key: str, default: Any = None) -> Any:
        """Retrieve a variable from ``os.environ`` with optional default."""
        return os.getenv(key.upper()) or default
