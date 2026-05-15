from __future__ import annotations

from pathlib import Path

from govflow_backend.responsible_ai.loader import load_responsible_ai_config


def test_load_responsible_ai_config() -> None:
    repo = Path(__file__).resolve().parents[2]
    cfg = load_responsible_ai_config(config_dir=repo / "config", environment="development")
    assert cfg.version >= 1
    assert cfg.rate_limiting.enabled is False
    assert cfg.guardrails.output_validation.enabled is True
