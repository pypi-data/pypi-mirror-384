from typing import Any, Dict, List, Optional, Type

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .authentication import Auth, auth_data_class_to_dependency
from .route import Route

__all__ = ("Router",)


class Router:
    def __init__(
        self,
        prefix: str = "",
        tags: List[str] = None,
        authentications: List[Auth] = None,
        dependencies: List[Any] = None,
        routes: List[Route] = None,
        responses: Optional[Dict[int, Dict[str, Any]]] = None,
        default_response_class: Optional[Type[Any]] = JSONResponse,
        include_in_schema: bool = True,
        deprecated: bool = False,
    ):
        """Initialize a Router instance and create the APIRouter."""

        dependencies = dependencies or []
        for authentication in authentications or []:
            dependencies.extend(auth_data_class_to_dependency(authentication))

        self.dependencies = dependencies

        self.prefix = prefix
        self.tags = tags or []
        self.routes = routes or []
        self.responses = responses
        self.default_response_class = default_response_class
        self.include_in_schema = include_in_schema
        self.deprecated = deprecated
        self.router = self._create_router()

    def _create_router(self) -> APIRouter:
        """Create an APIRouter dynamically based on the configuration."""

        router = APIRouter(
            prefix=self.prefix,
            tags=self.tags,
            dependencies=self.dependencies,
            responses=self.responses,
            default_response_class=self.default_response_class,
            include_in_schema=self.include_in_schema,
            deprecated=self.deprecated,
        )

        for route in self.routes:
            router.add_api_route(
                path=route.path,
                endpoint=route.wrapped_handler(),
                methods=[route.method.value],
                response_model=route.response_model,
                status_code=route.status_code,
                dependencies=route.dependencies,
                name=route.name,
                summary=route.summary,
                description=route.description,
                tags=route.tags,
                response_description=route.response_description,
                responses=route.responses,
                deprecated=route.deprecated,
                operation_id=route.operation_id,
                include_in_schema=route.include_in_schema,
                response_class=route.response_class,
                response_model_exclude_unset=route.response_model_exclude_unset,
                response_model_exclude_defaults=route.response_model_exclude_defaults,
                response_model_exclude_none=route.response_model_exclude_none,
                response_model_by_alias=route.response_model_by_alias,
            )
        return router

    def get_router(self) -> APIRouter:
        """Return the underlying :class:`APIRouter` instance."""
        return self.router
