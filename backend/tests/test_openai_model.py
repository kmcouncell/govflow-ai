from __future__ import annotations

from pathlib import Path

import pytest

from govflow_backend.config_loader import load_merged_file_config
from govflow_backend.core.config import get_settings
from govflow_backend.core.openai_model import resolve_openai_chat_model


def test_resolve_openai_chat_model_prefers_env_over_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_merged_file_config(config_dir=root / "config", environment="development")
    monkeypatch.setenv("GOVFLOW_OPENAI_MODEL", "env-model-override")
    get_settings.cache_clear()
    settings = get_settings()
    assert resolve_openai_chat_model(settings, cfg) == "env-model-override"


def test_resolve_yaml_default_when_model_env_cleared(monkeypatch: pytest.MonkeyPatch) -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_merged_file_config(config_dir=root / "config", environment="development")
    monkeypatch.delenv("GOVFLOW_OPENAI_MODEL", raising=False)
    get_settings.cache_clear()
    settings = get_settings()
    assert resolve_openai_chat_model(settings, cfg) == cfg.app.llm.default_chat_model
