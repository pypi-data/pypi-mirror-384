"""Enum definitions used across the framework."""

from enum import Enum

__all__ = ("OrderingType",)


class OrderingType(str, Enum):
    """Generic ascending/descending ordering options."""

    desc = "desc"
    asc = "asc"
