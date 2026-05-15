"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from govflow_backend.agents.loader import load_agents_prompt_config
from govflow_backend.api.deps import require_graph_api, require_rag_api
from govflow_backend.api.routers.graph import router as graph_router
from govflow_backend.api.routers.health import router as health_router
from govflow_backend.api.routers.rag import router as rag_router
from govflow_backend.config_loader import load_merged_file_config
from govflow_backend.config_models import MergedFileConfig
from govflow_backend.core.config import GovFlowSettings, get_settings
from govflow_backend.core.feature_flags import resolve_effective_feature_flags
from govflow_backend.core.logging import (
    CorrelationIdMiddleware,
    HttpAccessLogMiddleware,
    get_logger,
    setup_logging,
)
from govflow_backend.core.rate_limit import RateLimitMiddleware
from govflow_backend.core.request_metrics import RequestMetricsMiddleware
from govflow_backend.core.security import install_security_middleware
from govflow_backend.exceptions import (
    ConfigurationError,
    ExternalServiceError,
    GovFlowError,
    GuardrailsError,
    RagError,
)
from govflow_backend.graph.workflow import build_stub_graph
from govflow_backend.rag.factories import build_rag_runtime
from govflow_backend.rag.yaml_loader import load_rag_config
from govflow_backend.responsible_ai.loader import load_responsible_ai_config


def _build_openapi_description(*, settings: GovFlowSettings, file_config: MergedFileConfig) -> str:
    hdr = settings.correlation_id_request_header
    desc = file_config.app.description.strip()
    return f"""{desc}

## Operations notes

- **Correlation IDs**: send `{hdr}`; the API echoes it on responses for log correlation.
- **Responsible AI**: user questions, streaming aggregates, and assistant output are evaluated
  against the configured policy pack under `config/responsible_ai.*.yaml`.

## Representative requests

### `POST /v1/rag/query`

```json
{{
  "question": "What is covered in the onboarding sample document?",
  "top_k": 4
}}
```

### `POST /v1/graph/invoke`

```json
{{
  "messages": [{{"role": "user", "content": "Draft a concise status update."}}],
  "thread_id": "demo-thread-001"
}}
```

### `POST /v1/rag/ingest`

```json
{{
  "reset": false
}}
```
"""


def register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(RagError)
    async def _rag_error(_: Request, exc: RagError) -> JSONResponse:
        get_logger(__name__).warning("rag_error", error=str(exc))
        return JSONResponse(status_code=400, content={"detail": "rag_error", "message": str(exc)})

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

    @application.exception_handler(GuardrailsError)
    async def _guardrails_error(_: Request, exc: GuardrailsError) -> JSONResponse:
        get_logger(__name__).warning("guardrails_error", error=str(exc), flags=exc.flags)
        return JSONResponse(
            status_code=400,
            content={
                "detail": "guardrails_violation",
                "message": str(exc),
                "flags": exc.flags,
            },
        )

    @application.exception_handler(GovFlowError)
    async def _govflow_error(_: Request, exc: GovFlowError) -> JSONResponse:
        get_logger(__name__).error("govflow_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "internal_error", "message": str(exc)},
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
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
    app.state.agents_prompts = load_agents_prompt_config(
        config_dir=settings.resolved_config_dir,
        environment=settings.environment,
    )
    app.state.graph = build_stub_graph(settings, file_config, app.state.agents_prompts)
    app.state.rag_runtime = build_rag_runtime(settings, app.state.rag_yaml)
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
        description=_build_openapi_description(settings=settings, file_config=file_config),
        openapi_url=file_config.app.api.openapi_url if file_config.app.api.docs_enabled else None,
        lifespan=lifespan,
        root_path=settings.backend_root_path or "",
        openapi_tags=[
            {
                "name": "health",
                "description": "Liveness/readiness probes and request correlation headers.",
            },
            {
                "name": "graph",
                "description": "LangGraph supervisor demo, synchronous invoke, and SSE streaming.",
            },
            {
                "name": "rag",
                "description": "RAG ingestion and grounded QA over the configured vector store.",
            },
        ],
    )
    application.state.settings = settings
    application.state.file_config = file_config
    application.state.effective_feature_flags = resolve_effective_feature_flags(
        settings,
        file_config.features,
    )
    application.state.rag_yaml = load_rag_config(
        config_dir=settings.resolved_config_dir,
        environment=settings.environment,
    )
    application.state.responsible_ai = load_responsible_ai_config(
        config_dir=settings.resolved_config_dir,
        environment=settings.environment,
    )

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
    application.add_middleware(RequestMetricsMiddleware)
    application.add_middleware(RateLimitMiddleware)

    application.include_router(health_router, prefix="/health", tags=["health"])
    application.include_router(
        graph_router,
        prefix="/v1/graph",
        tags=["graph"],
        dependencies=[Depends(require_graph_api)],
    )
    application.include_router(
        rag_router,
        prefix="/v1/rag",
        tags=["rag"],
        dependencies=[Depends(require_rag_api)],
    )

    return application


app = create_app()
