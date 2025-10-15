import time
from typing import Callable

from fastapi import Request, Response

__all__ = ("Timer",)


class Timer:

    def __init__(self):
        pass

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        response.headers["X-Process-Time"] = str(
            round((time.time() - start_time) * 1000)
        )
        return response
