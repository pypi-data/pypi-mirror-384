"""Helpers for normalising strings into URL slugs."""

import re
import unicodedata

__all__ = ("create_slug",)


def create_slug(name: str) -> str | None:
    """Return a URL-friendly slug derived from ``name``."""

    if not name:
        return None

    # Convert to lowercase and replace spaces with hyphens
    slug = name.lower().replace(" ", "-")

    # Remove any characters that are not letters, numbers, hyphens, or underscores
    slug = re.sub(r"[^a-zA-Z0-9\-_]", "", slug)

    # Normalize the slug to remove any diacritic marks
    slug = unicodedata.normalize("NFKD", slug).encode("ascii", "ignore").decode("utf-8")

    # Remove any leading or trailing hyphens
    slug = slug.strip("-")

    return slug
