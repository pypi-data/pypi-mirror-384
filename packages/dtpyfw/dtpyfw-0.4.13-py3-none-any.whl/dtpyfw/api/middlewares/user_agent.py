from typing import Callable

from fastapi import Request, Response

from ...core.exception import RequestException

__all__ = ("InternalUserAgentRestriction",)


class InternalUserAgentRestriction:
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        controller = f"{__name__}.InternalUserAgentRestriction.__call__"
        ua = request.headers.get("user-agent") or ""
        if ua != "DealerTower-Service/1.0":
            raise RequestException(
                controller=controller,
                message="Wrong credential.",
                status_code=403,
            )
