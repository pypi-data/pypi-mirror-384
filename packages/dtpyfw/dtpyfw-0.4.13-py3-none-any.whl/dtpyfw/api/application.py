"""High-level FastAPI application wrapper and configuration helpers."""

from typing import Any, Dict, Optional, Sequence, Tuple, Union

from fastapi import FastAPI
from starlette.requests import Request

from .middlewares import http_exception, runtime, timer, validation_exception
from .middlewares.user_agent import InternalUserAgentRestriction
from .routes.router import Router

__all__ = ("Application",)


class Application:
    """Wrapper for configuring a FastAPI app using clean OOP structure."""

    def __init__(
        self,
        title: str,
        version: str = "*",
        redoc_url: Optional[str] = "/",
        docs_url: Optional[str] = "/swagger",
        applications: Optional[Sequence[Tuple[str, "Application"]]] = None,
        routers: Optional[
            Union[Sequence[Tuple[str, Sequence[Router]]], Sequence[Router]]
        ] = None,
        gzip_min_size: Optional[int] = None,
        session_middleware_settings: Optional[Dict[str, Any]] = None,
        middlewares: Optional[Sequence[Any]] = None,
        only_internal_user_agent: Optional[bool] = False,
        lifespan: Optional[Any] = None,
        cors_settings: Optional[Dict[str, Any]] = None,
        hide_error_messages: bool = True,
    ) -> None:
        """Initialize the application wrapper."""
        # Core metadata
        self.title = title
        self.version = version
        self.redoc_url = redoc_url
        self.docs_url = docs_url
        self.lifespan = lifespan

        # Sub-apps and routers
        self.applications = applications or ()
        self.routers = routers or ()

        # Middleware configuration
        base_mws = list(middlewares or [])
        if only_internal_user_agent:
            base_mws.insert(0, InternalUserAgentRestriction())

        self.middlewares = (
            timer.Timer(),
            runtime.Runtime(hide_error_messages),
            *base_mws,
        )

        self.gzip_min_size = gzip_min_size
        self.session_settings = session_middleware_settings or {}

        # CORS defaults and overrides
        self.cors_settings: Dict[str, Any] = {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
            "expose_headers": [],
            "allow_origin_regex": None,
            "max_age": 600,
        }
        if cors_settings:
            self.cors_settings.update(cors_settings)

        # Build the FastAPI instance
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """Create and configure the internal :class:`FastAPI` instance."""
        app = FastAPI(
            title=self.title,
            version=self.version,
            redoc_url=self.redoc_url,
            docs_url=self.docs_url,
            swagger_ui_parameters={"defaultModelsExpandDepth": -1},
            lifespan=self.lifespan,
        )
        self._configure_gzip(app)
        self._configure_middlewares(app)
        self._configure_session(app)
        self._configure_cors(app)
        self._configure_exception_handlers(app)
        self._mount_sub_applications(app)
        self._include_routers(app)
        return app

    def _configure_gzip(self, app: FastAPI) -> None:
        """Configure gzip compression for the app if enabled."""
        if self.gzip_min_size is not None:
            from fastapi.middleware.gzip import GZipMiddleware

            app.add_middleware(GZipMiddleware, minimum_size=self.gzip_min_size)

    def _configure_session(self, app: FastAPI) -> None:
        """Attach the session middleware when settings are provided."""
        if self.session_settings:
            from starlette.middleware.sessions import SessionMiddleware

            app.add_middleware(SessionMiddleware, **self.session_settings)

    def _configure_middlewares(self, app: FastAPI) -> None:
        """Register custom middlewares with the app."""
        if self.middlewares:
            from starlette.middleware.base import BaseHTTPMiddleware

            for mw in self.middlewares:
                app.add_middleware(BaseHTTPMiddleware, dispatch=mw)

    def _configure_cors(self, app: FastAPI) -> None:
        """Apply CORS settings to the app."""
        if self.cors_settings:
            from fastapi.middleware.cors import CORSMiddleware

            app.add_middleware(CORSMiddleware, **self.cors_settings)

    def _configure_exception_handlers(self, app: FastAPI) -> None:
        """Register common exception handlers with the app."""
        from starlette.exceptions import HTTPException as StarletteHTTPException

        @app.exception_handler(StarletteHTTPException)
        async def _http_exception_handler(
            request: Request, exc: StarletteHTTPException
        ) -> Any:
            """Handle HTTP exceptions using the shared utility."""
            return await http_exception.http_exception_handler(request, exc)

        from fastapi.exceptions import RequestValidationError

        @app.exception_handler(RequestValidationError)
        async def _validation_exception_handler(
            request: Request, exc: RequestValidationError
        ) -> Any:
            """Handle request validation exceptions."""
            return await validation_exception.validation_exception_handler(request, exc)

    def _mount_sub_applications(self, app: FastAPI) -> None:
        """Mount nested applications under the configured prefixes."""
        for prefix, sub_app in self.applications:
            app.mount(prefix, sub_app.get_app())

    def _include_routers(self, app: FastAPI) -> None:
        """Include routers under their prefixes if specified."""
        for item in self.routers:
            if isinstance(item, tuple):
                prefix, routers = item
                for router in routers:
                    app.include_router(
                        router=router.get_router(),
                        prefix=prefix,
                    )
            else:
                app.include_router(
                    router=item.get_router(),
                )

    def get_app(self) -> FastAPI:
        """Return the fully configured FastAPI application."""
        return self.app
