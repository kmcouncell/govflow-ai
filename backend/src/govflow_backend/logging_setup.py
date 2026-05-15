"""Structured logging setup (structlog + stdlib), driven by settings and YAML."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from govflow_backend.config_models import MergedFileConfig
    from govflow_backend.settings import GovFlowSettings


def setup_logging(settings: GovFlowSettings, file_config: MergedFileConfig) -> None:
    """Configure structlog and stdlib logging from env + YAML."""

    log_cfg = file_config.logging
    service_name = str(log_cfg.get("service_name", "govflow-backend"))
    json_logs = settings.log_json

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.PositionalArgumentsFormatter(),
    ]

    if json_logs:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

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
    root.setLevel(settings.log_level.upper())

    logging.getLogger("uvicorn.error").setLevel(settings.log_level.upper())
    logging.getLogger("uvicorn.access").setLevel(settings.log_level.upper())

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name, env=settings.environment)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog-bound stdlib logger."""

    return structlog.get_logger(name)
