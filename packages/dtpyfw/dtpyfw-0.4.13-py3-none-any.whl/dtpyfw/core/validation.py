import re
from urllib.parse import urlparse
from uuid import UUID

__all__ = (
    "is_email",
    "is_vin",
    "is_year",
    "is_uuid",
    "is_valid_http_url",
)


def is_email(email: str) -> bool:
    import re

    return (
        True
        if re.fullmatch(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", email)
        else False
    )


def is_vin(vin) -> bool:
    vin_pattern = "[A-HJ-NPR-Z0-9]{17}"
    return bool(re.match(vin_pattern, vin))


def is_year(s: str) -> bool:
    if len(s) != 4:
        return False
    try:
        year = int(s)
        if year < 1:
            return False
    except ValueError:
        return False
    return True


def is_uuid(uuid_to_test, version=4) -> bool:
    if isinstance(uuid_to_test, UUID):
        return True

    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def is_valid_http_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False
