from dataclasses import dataclass
from enum import Enum
from typing import List

from fastapi import Depends, Request
from fastapi.security import APIKeyHeader, APIKeyQuery

from ...core.exception import RequestException

__all__ = (
    "AuthType",
    "Auth",
    "auth_data_class_to_dependency",
)


class AuthType(Enum):
    HEADER = "header"
    QUERY = "query"


@dataclass
class Auth:
    auth_type: AuthType
    header_key: str | None = None
    real_value: str | None = None


class HeaderAuthChecker:
    def __init__(self, key: str, real_value: str):
        self.key = key
        self.real_value = real_value

    def __call__(self, request: Request):
        controller = f"{__name__}.HeaderAuthChecker.__call__"
        auth_token = request.headers.get(self.key)
        if auth_token is None or auth_token != self.real_value:
            raise RequestException(
                controller=controller,
                message="Wrong credential.",
                status_code=403,
            )


class QueryAuthChecker:
    def __init__(self, key: str, real_value: str):
        self.key = key
        self.real_value = real_value

    def __call__(self, request: Request):
        controller = f"{__name__}.QueryAuthChecker.__call__"
        auth_token = request.query_params.get(self.key)
        if auth_token is None or auth_token != self.real_value:
            raise RequestException(
                controller=controller,
                message="Wrong credential.",
                status_code=403,
            )


def auth_data_class_to_dependency(authentication: Auth) -> List[Depends]:
    """
    Convert an Auth configuration into a list of FastAPI dependencies.

    Behavior
    - For AuthType.HEADER: returns two dependencies:
        1. `Depends(HeaderAuthChecker(...))` — runtime checker that validates the incoming header value.
        2. `Depends(APIKeyHeader(name=...))` — exposes the header in OpenAPI/Swagger (so the docs show the required header).
    - For AuthType.QUERY: returns two dependencies:
        1. `Depends(QueryAuthChecker(...))` — runtime checker that validates the incoming query parameter.
        2. `Depends(APIKeyQuery(name=...))` — exposes the query param in OpenAPI/Swagger.
    - For any other/unsupported auth_type, returns an empty list.

    Parameters
    ----------
    authentication : Auth
        An `Auth` configuration object containing at least:
         - `auth_type` (AuthType) — which transport to use (HEADER or QUERY),
         - `header_key` (str) — the header / query parameter name,
         - `real_value` (str) — the expected secret value used by the checker.

    Returns
    -------
    List[Depends]
        A list of FastAPI dependency objects suitable for inclusion in an endpoint signature.
        The pair (checker + APIKey dependency) is intentionally provided so the checker enforces
        runtime validation while the APIKey* dependency registers the parameter in OpenAPI.
    """
    if authentication.auth_type == AuthType.HEADER:
        checker = HeaderAuthChecker(
            key=authentication.header_key, real_value=authentication.real_value
        )
        return [
            Depends(checker),
            Depends(APIKeyHeader(
                name=authentication.header_key,
                description=f"API key header '{authentication.header_key}' required for access."
            )),
        ]
    elif authentication.auth_type == AuthType.QUERY:
        checker = QueryAuthChecker(
            key=authentication.header_key, real_value=authentication.real_value
        )
        return [
            Depends(checker),
            Depends(APIKeyQuery(
                name=authentication.header_key,
                description=f"API key query parameter '{authentication.header_key}' required for access."
            )),
        ]

    return []
