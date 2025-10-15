from typing import Any, Callable, Dict

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ...core.exception import RequestException, exception_to_dict
from ...log import footprint
from ..routes.response import return_response

__all__ = ("Runtime",)


class Runtime:

    def __init__(self, hide_error_messages: bool = True) -> None:
        self.hide_error_messages = hide_error_messages

    @staticmethod
    async def get_request_body(request: Request) -> Dict[str, Any]:
        content_length = request.headers.get("content-length")
        content_type = request.headers.get("content-type")
        try:
            if content_length and int(content_length) > (1 * 1024 * 1024):
                return {}
            body = await request.body()
            return {
                "content_length": content_length,
                "content_type": content_type,
                "json": jsonable_encoder(body.decode("utf-8")),
            }
        except Exception:
            return {
                "content_length": content_length,
                "content_type": content_type,
            }

    @staticmethod
    async def create_payload(request: Request, exception: Exception) -> Dict[str, Any]:
        body = await Runtime.get_request_body(request)
        return jsonable_encoder(
            {
                "path": request.url.path,
                "method": request.method,
                "query_parameters": request.query_params,
                "path_parameters": request.path_params,
                "headers": request.headers,
                "body": body,
                **exception_to_dict(exception),
            }
        )

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        controller = f"{__name__}.Runtime.__call__"
        try:
            response = await call_next(request)
        except RequestException as e:
            payload = await self.create_payload(request, e)
            if not e.skip_footprint:
                footprint.leave(
                    log_type="warning",
                    message=e.message,
                    controller=e.controller,
                    subject="Request Error",
                    payload=payload,
                )

            return return_response(
                data=str(e.message),
                status_code=e.status_code,
                response_class=JSONResponse,
            )
        except Exception as e:
            payload = await self.create_payload(request, e)
            try:
                message = str(e)
            except:
                message = "Unrecognized Error has happened."

            footprint.leave(
                log_type="error",
                message=message,
                controller=controller,
                subject="Unrecognized Error",
                payload=payload,
            )

            return return_response(
                data=(
                    "An unexpected issue has occurred; our team has been notified and is working diligently to resolve it promptly."
                    if self.hide_error_messages
                    else message
                ),
                status_code=500,
                response_class=JSONResponse,
            )
        else:
            return response
