"""Wrapper objects used to build FastAPI routing configuration."""

import inspect
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, create_model

from ..schemas.response import FailedResponse, ResponseBase, SuccessResponse
from .authentication import Auth, auth_data_class_to_dependency
from .response import return_response

__all__ = (
    "RouteMethod",
    "Route",
)


class RouteMethod(Enum):
    GET = "GET"
    PUT = "PUT"
    POST = "POST"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    CONNECT = "CONNECT"


class Route:
    """Single FastAPI route configuration."""

    def __init__(
        self,
        path: str,
        method: RouteMethod,
        handler: Callable,
        wrapping_handler: bool = True,
        authentications: List[Auth] = None,
        response_model: Optional[Type[BaseModel]] = None,
        default_response_model: Optional[Any] = None,
        wrapping_response_model: bool = True,
        status_code: int = 200,
        errors: Dict[int, str] = None,
        dependencies: List[Any] = None,
        wrapper_kwargs: Dict[str, Any] = None,
        name: Optional[str] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[int, Dict[str, Any]]] = None,
        deprecated: bool = False,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        response_class: Optional[Type[Response]] = JSONResponse,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        response_model_by_alias: bool = True,
        response_return_json_directly: bool = False,
        response_headers: Dict[int, Dict] = None,
        response_no_cache_headers: bool = True,
    ):
        """Create a Route definition.

        Parameters mirror ``fastapi.APIRouter.add_api_route`` with additional
        options for automatic authentication and success/error response models.
        """
        dependencies = dependencies or []
        for authentication in authentications or []:
            dependencies.extend(auth_data_class_to_dependency(authentication))

        self.dependencies = dependencies

        if responses:
            if 422 not in responses:
                responses.update(
                    {
                        422: {
                            "model": FailedResponse,
                        }
                    }
                )
        else:
            errors = errors or {}
            if 422 not in errors:
                errors[422] = "Validation Error"

            responses = {
                status_error: {
                    "model": create_model(
                        "FailedResponse",
                        __base__=ResponseBase,
                        success=(bool, False),
                        message=(str, error_message),
                    )
                }
                for status_error, error_message in errors.items()
            }

        if wrapping_response_model:
            model_name = getattr(response_model, "__name__", "SuccessfulResponse")
            data_type = response_model or Any
            default_value = (
                default_response_model if default_response_model is not None else ...
            )
            self.response_model = create_model(
                model_name,
                __base__=SuccessResponse,
                **{"data": (data_type, default_value)},
            )
        else:
            self.response_model = response_model or SuccessResponse

        self.path = path
        self.method = method
        self.handler = handler
        self.wrapping_handler = wrapping_handler
        self.status_code = status_code
        self.wrapper_kwargs = wrapper_kwargs or {}
        self.name = name
        self.summary = summary
        self.description = description
        self.tags = tags
        self.response_description = response_description
        self.responses = responses
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.include_in_schema = include_in_schema
        self.response_class = response_class
        self.response_model_exclude_unset = response_model_exclude_unset
        self.response_model_exclude_defaults = response_model_exclude_defaults
        self.response_model_exclude_none = response_model_exclude_none
        self.response_model_by_alias = response_model_by_alias
        self.response_return_json_directly = response_return_json_directly
        self.response_headers = response_headers
        self.response_no_cache_headers = response_no_cache_headers

    def wrapped_handler(self) -> Callable:
        """Return a handler that automatically formats the response."""
        is_async = inspect.iscoroutinefunction(self.handler)

        def wrap_function(wrapped_func: Callable) -> Callable:
            @wraps(wrapped_func)
            async def async_wrapper(*args, **kwargs):
                result = await wrapped_func(*args, **kwargs)
                if self.wrapping_handler:
                    return return_response(
                        data=result,
                        status_code=self.status_code,
                        response_class=self.response_class,
                        return_json_directly=self.response_return_json_directly,
                        headers=self.response_headers,
                        no_cache=self.response_no_cache_headers,
                    )
                else:
                    return result

            @wraps(wrapped_func)
            def sync_wrapper(*args, **kwargs):
                result = wrapped_func(*args, **kwargs)
                if self.wrapping_handler:
                    return return_response(
                        data=result,
                        status_code=self.status_code,
                        response_class=self.response_class,
                        return_json_directly=self.response_return_json_directly,
                        headers=self.response_headers,
                        no_cache=self.response_no_cache_headers,
                    )
                else:
                    return result

            return async_wrapper if is_async else sync_wrapper

        return wrap_function(self.handler)
