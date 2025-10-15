"""Small URL manipulation helpers."""

from typing import Dict, Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

__all__ = ("add_query_param",)


def add_query_param(url: str, params: Dict[str, Any]) -> str:
    """Return ``url`` with additional query string parameters."""

    url_parts = urlparse(url)
    query_params = parse_qs(url_parts.query)
    query_params.update(params)
    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse(
        (
            url_parts.scheme,
            url_parts.netloc,
            url_parts.path,
            url_parts.params,
            new_query,
            url_parts.fragment,
        )
    )
    return new_url
