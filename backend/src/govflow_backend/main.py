"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from govflow_backend.api.routers.graph import router as graph_router
from govflow_backend.api.routers.health import router as health_router
from govflow_backend.config_loader import load_merged_file_config
from govflow_backend.config_models import MergedFileConfig
from govflow_backend.core.config import GovFlowSettings, get_settings
from govflow_backend.core.logging import (
    CorrelationIdMiddleware,
    HttpAccessLogMiddleware,
    get_logger,
    setup_logging,
)
from govflow_backend.core.security import install_security_middleware
from govflow_backend.exceptions import ConfigurationError, ExternalServiceError, GovFlowError
from govflow_backend.graph.workflow import build_stub_graph


def register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(ConfigurationError)
    async def _configuration_error(_: Request, exc: ConfigurationError) -> JSONResponse:
        get_logger(__name__).exception("configuration_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "configuration_error", "message": str(exc)},
        )

    @application.exception_handler(ExternalServiceError)
    async def _external_error(_: Request, exc: ExternalServiceError) -> JSONResponse:
        get_logger(__name__).warning("external_service_error", error=str(exc))
        return JSONResponse(
            status_code=503,
            content={"detail": "external_service_unavailable", "message": str(exc)},
        )

    @application.exception_handler(GovFlowError)
    async def _govflow_error(_: Request, exc: GovFlowError) -> JSONResponse:
        get_logger(__name__).error("govflow_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "internal_error", "message": str(exc)},
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: GovFlowSettings = app.state.settings
    file_config: MergedFileConfig = app.state.file_config
    settings.resolved_log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(settings, file_config)
    log = get_logger(__name__)
    log.info(
        "startup_complete",
        environment=settings.environment,
        config_dir=str(settings.resolved_config_dir),
    )
    app.state.graph = build_stub_graph(settings, file_config)
    yield
    log.info("shutdown_complete")


def create_app() -> FastAPI:
    settings = get_settings()
    file_config = load_merged_file_config(
        config_dir=settings.resolved_config_dir,
        environment=settings.environment,
    )

    application = FastAPI(
        title=file_config.app.api.title,
        version=file_config.app.api.version,
        openapi_url=file_config.app.api.openapi_url if file_config.app.api.docs_enabled else None,
        lifespan=lifespan,
        root_path=settings.backend_root_path or "",
    )
    application.state.settings = settings
    application.state.file_config = file_config

    register_exception_handlers(application)

    # Middleware: first registered is innermost; last is outermost on the request path.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=file_config.app.cors.allow_credentials,
        allow_methods=file_config.app.cors.allow_methods,
        allow_headers=file_config.app.cors.allow_headers,
    )
    application.add_middleware(HttpAccessLogMiddleware, settings=settings)
    application.add_middleware(CorrelationIdMiddleware, settings=settings)
    install_security_middleware(application, settings)

    application.include_router(health_router, prefix="/health", tags=["health"])
    application.include_router(graph_router, prefix="/v1/graph", tags=["graph"])

    return application


app = create_app()
