from __future__ import annotations

from pathlib import Path

from govflow_backend.config_loader import load_merged_file_config


def test_load_merged_file_config_resolves_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_merged_file_config(config_dir=root / "config", environment="development")
    assert cfg.app.api.title
    assert cfg.features.llm_enabled is False
