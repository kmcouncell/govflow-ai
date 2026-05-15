"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from govflow_backend.config_loader import load_merged_file_config
from govflow_backend.config_models import MergedFileConfig
from govflow_backend.exceptions import ConfigurationError, ExternalServiceError, GovFlowError
from govflow_backend.graph.workflow import build_stub_graph
from govflow_backend.logging_setup import get_logger, setup_logging
from govflow_backend.settings import GovFlowSettings, get_settings


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

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=file_config.app.cors.allow_credentials,
        allow_methods=file_config.app.cors.allow_methods,
        allow_headers=file_config.app.cors.allow_headers,
    )

    @application.exception_handler(ConfigurationError)
    async def _configuration_error(_: Request, exc: ConfigurationError) -> JSONResponse:
        get_logger(__name__).exception("configuration_error", error=str(exc))
        return JSONResponse(status_code=500, content={"detail": "configuration_error", "message": str(exc)})

    @application.exception_handler(ExternalServiceError)
    async def _external_error(_: Request, exc: ExternalServiceError) -> JSONResponse:
        get_logger(__name__).warning("external_service_error", error=str(exc))
        return JSONResponse(status_code=503, content={"detail": "external_service_unavailable", "message": str(exc)})

    @application.exception_handler(GovFlowError)
    async def _govflow_error(_: Request, exc: GovFlowError) -> JSONResponse:
        get_logger(__name__).error("govflow_error", error=str(exc))
        return JSONResponse(status_code=500, content={"detail": "internal_error", "message": str(exc)})

    @application.get("/health/live", tags=["health"])
    async def health_live() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/ready", tags=["health"])
    async def health_ready(request: Request) -> dict[str, Any]:
        cfg: GovFlowSettings = request.app.state.settings
        return {
            "status": "ok",
            "environment": cfg.environment,
            "sample_data_dir_exists": cfg.resolved_sample_data_dir.is_dir(),
        }

    @application.post("/v1/graph/demo", tags=["graph"])
    async def graph_demo(request: Request) -> dict[str, Any]:
        graph = request.app.state.graph
        result = await graph.ainvoke({"messages": [], "step_count": 0})
        return {"result": result}

    return application


app = create_app()
