from __future__ import annotations

import pytest

from govflow_backend.core.config import get_settings
from govflow_backend.exceptions import ConfigurationError, RagError
from govflow_backend.rag.factories import build_embedding_client, build_vector_store
from govflow_backend.rag.vector_store.pgvector import PgVectorVectorStore


def test_build_embedding_client_fake() -> None:
    settings = get_settings()
    client = build_embedding_client(settings, prefer_fake=True)
    v = client.embed_query("hello")
    assert len(v) == settings.rag_embedding_dimensions


def test_build_vector_store_chroma() -> None:
    from govflow_backend.rag.vector_store.chroma import ChromaVectorStore

    settings = get_settings()
    store = build_vector_store(settings)
    assert isinstance(store, ChromaVectorStore)


def test_pgvector_store_rejects_empty_dsn() -> None:
    with pytest.raises(RagError):
        PgVectorVectorStore(dsn="   ", collection_id="c", dimensions=8)


def test_unknown_vector_backend() -> None:
    import os

    os.environ["GOVFLOW_RAG_VECTOR_BACKEND"] = "not-a-backend"
    get_settings.cache_clear()
    try:
        s = get_settings()
        with pytest.raises(ConfigurationError):
            build_vector_store(s)
    finally:
        os.environ["GOVFLOW_RAG_VECTOR_BACKEND"] = "chroma"
        get_settings.cache_clear()
