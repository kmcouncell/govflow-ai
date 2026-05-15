from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from govflow_backend.core.config import get_settings
from govflow_backend.core.feature_flags import (
    EffectiveFeatureFlags,
    resolve_effective_feature_flags,
)
from govflow_backend.main import create_app


def test_resolve_effective_feature_flags_uses_yaml_defaults() -> None:
    from pathlib import Path

    from govflow_backend.config_loader import load_merged_file_config

    root = Path(__file__).resolve().parents[2]
    cfg = load_merged_file_config(config_dir=root / "config", environment="development")
    flags = resolve_effective_feature_flags(get_settings(), cfg.features)
    assert isinstance(flags, EffectiveFeatureFlags)
    assert flags.rag_api_enabled is True
    assert flags.graph_api_enabled is True


def test_graph_api_disabled_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOVFLOW_FEATURE_GRAPH_API_ENABLED", "false")
    get_settings.cache_clear()
    application = create_app()
    try:
        with TestClient(application) as client:
            response = client.post("/v1/graph/demo")
            assert response.status_code == 503
            body = response.json()
            assert body["detail"]["detail"] == "feature_disabled"
            assert body["detail"]["feature"] == "graph_api"
    finally:
        monkeypatch.delenv("GOVFLOW_FEATURE_GRAPH_API_ENABLED", raising=False)
        get_settings.cache_clear()


def test_rag_api_disabled_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOVFLOW_FEATURE_RAG_API_ENABLED", "false")
    get_settings.cache_clear()
    application = create_app()
    try:
        with TestClient(application) as client:
            response = client.post("/v1/rag/ingest", json={"reset": False})
            assert response.status_code == 503
            body = response.json()
            assert body["detail"]["detail"] == "feature_disabled"
            assert body["detail"]["feature"] == "rag_api"
    finally:
        monkeypatch.delenv("GOVFLOW_FEATURE_RAG_API_ENABLED", raising=False)
        get_settings.cache_clear()
