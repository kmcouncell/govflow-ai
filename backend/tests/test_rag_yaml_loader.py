from __future__ import annotations

from pathlib import Path

from govflow_backend.rag.schema import RagYamlRoot
from govflow_backend.rag.yaml_loader import load_rag_config


def test_load_rag_config_merges_development_overlay() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_rag_config(config_dir=root / "config", environment="development")
    assert isinstance(cfg, RagYamlRoot)
    assert cfg.retrieval.default_top_k == 5
    assert len(cfg.prompts.generative_system) > 10
