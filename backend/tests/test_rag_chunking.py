from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document

from govflow_backend.rag.chunking import build_recursive_splitter, split_rag_documents
from govflow_backend.rag.yaml_loader import load_rag_config


def test_recursive_splitter_respects_yaml_sizes() -> None:
    root = Path(__file__).resolve().parents[2]
    rag = load_rag_config(config_dir=root / "config", environment="development")
    splitter = build_recursive_splitter(rag.chunking)
    long_text = "word " * 200
    docs = [Document(page_content=long_text, metadata={"doc_id": "x"})]
    chunks = split_rag_documents(documents=docs, splitter=splitter)
    assert len(chunks) >= 2
    assert all(len(c.page_content) <= rag.chunking.chunk_size + 20 for c in chunks)
