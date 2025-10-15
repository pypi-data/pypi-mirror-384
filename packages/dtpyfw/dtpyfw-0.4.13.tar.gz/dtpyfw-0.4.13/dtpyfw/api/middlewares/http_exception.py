from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from ..routes.response import return_response

__all__ = ("http_exception_handler",)


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> return_response:
    status_code = exc.status_code
    detail = request.url.path if status_code == 404 else exc.detail
    return return_response(
        data=str(detail),
        status_code=status_code,
        response_class=JSONResponse,
    )
