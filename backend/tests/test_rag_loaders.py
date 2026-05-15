from __future__ import annotations

import os
from pathlib import Path

from govflow_backend.rag.loaders import load_raw_documents
from govflow_backend.rag.yaml_loader import load_rag_config


def test_loaders_resolve_env_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    rag = load_rag_config(config_dir=root / "config", environment="development")
    os.environ["GOVFLOW_RAG_SOURCE_DIR"] = str(root / "sample_data" / "rag_docs")
    docs = load_raw_documents(rag.ingestion)
    assert docs, "expected at least one document from sample_data/rag_docs"
    assert any("GovFlow" in d.content for d in docs)
