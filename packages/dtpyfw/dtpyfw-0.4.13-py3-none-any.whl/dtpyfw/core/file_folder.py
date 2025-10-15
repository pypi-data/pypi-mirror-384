"""Small file and directory utilities."""

import os

__all__ = (
    "make_directory",
    "folder_path_of_file",
    "remove_file",
)


def make_directory(path: str) -> None:
    """Create ``path`` if it does not already exist."""

    if not os.path.exists(path):
        os.makedirs(path)


def folder_path_of_file(path: str) -> str:
    """Return the directory portion of a file path."""

    return os.path.dirname(os.path.realpath(path))


def remove_file(path: str) -> None:
    """Delete ``path`` if it exists."""

    if os.path.exists(path):
        os.remove(path)
