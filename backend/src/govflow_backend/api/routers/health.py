"""Kubernetes-style health endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/live", summary="Liveness probe")
async def health_live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
async def health_ready(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    return {
        "status": "ok",
        "environment": settings.environment,
        "sample_data_dir_exists": settings.resolved_sample_data_dir.is_dir(),
    }
