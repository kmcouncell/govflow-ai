"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import HTTPException, Request

from govflow_backend.core.feature_flags import EffectiveFeatureFlags


def _flags(request: Request) -> EffectiveFeatureFlags:
    raw = getattr(request.app.state, "effective_feature_flags", None)
    if not isinstance(raw, EffectiveFeatureFlags):
        raise HTTPException(status_code=500, detail="feature_flags_uninitialized")
    return raw


def require_graph_api(request: Request) -> None:
    if not _flags(request).graph_api_enabled:
        raise HTTPException(
            status_code=503,
            detail={
                "detail": "feature_disabled",
                "feature": "graph_api",
                "message": "Graph HTTP endpoints are disabled via configuration.",
            },
        )


def require_rag_api(request: Request) -> None:
    if not _flags(request).rag_api_enabled:
        raise HTTPException(
            status_code=503,
            detail={
                "detail": "feature_disabled",
                "feature": "rag_api",
                "message": "RAG HTTP endpoints are disabled via configuration.",
            },
        )
