from typing import Any, Generator, List

__all__ = (
    "chunk_list",
    "chunk_list_generator",
)


def chunk_list(lst: List[Any], chunk_size: int) -> List[Any]:
    """Splits a list into chunks of a specified size."""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def chunk_list_generator(
    lst: List[Any], chunk_size: int
) -> Generator[List[Any], None, None]:
    """Generates chunks of a specified size from a list."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]
