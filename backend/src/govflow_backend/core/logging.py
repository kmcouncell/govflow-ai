"""Structured logging, correlation IDs, and HTTP access instrumentation."""

from __future__ import annotations

import logging
import sys
import time
import uuid
from typing import TYPE_CHECKING

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from govflow_backend.config_models import MergedFileConfig
    from govflow_backend.core.config import GovFlowSettings


def _correlation_fallback_processor(
    _logger: logging.Logger,
    _method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    event_dict.setdefault("correlation_id", "-")
    return event_dict


def setup_logging(settings: GovFlowSettings, file_config: MergedFileConfig) -> None:
    """Configure structlog + stdlib logging (JSON when `settings.log_json`)."""

    log_cfg = file_config.logging
    service_name = str(log_cfg.get("service_name", "govflow-backend"))

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
        _correlation_fallback_processor,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.PositionalArgumentsFormatter(),
    ]

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if settings.log_json
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[
            *shared,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(settings.log_level)

    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.setLevel(settings.log_level)

    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.setLevel(settings.log_level if settings.log_uvicorn_access else logging.WARNING)

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name, env=settings.environment)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Bind `correlation_id` for structured logs and echo the ID on the response."""

    def __init__(self, app, settings: GovFlowSettings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request: Request, call_next) -> Response:
        header_name = self._settings.correlation_id_request_header
        incoming = request.headers.get(header_name)
        correlation_id = incoming.strip() if incoming and incoming.strip() else str(uuid.uuid4())

        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            http_method=request.method,
            http_path=request.url.path,
        )
        request.state.correlation_id = correlation_id
        try:
            response = await call_next(request)
            response.headers[self._settings.correlation_id_response_header] = correlation_id
            return response
        finally:
            structlog.contextvars.unbind_contextvars(
                "correlation_id",
                "http_method",
                "http_path",
            )


class HttpAccessLogMiddleware(BaseHTTPMiddleware):
    """Emits one structured log line per request when enabled in settings."""

    def __init__(self, app, settings: GovFlowSettings) -> None:
        super().__init__(app)
        self._settings = settings
        self._log = get_logger("govflow.http")

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self._settings.http_access_log_enabled:
            return await call_next(request)

        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 3)
            status = getattr(response, "status_code", 500) if response is not None else 500
            self._log.info(
                "http_request",
                duration_ms=duration_ms,
                status_code=status,
                client_host=request.client.host if request.client else None,
            )
