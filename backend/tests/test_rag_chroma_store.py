from __future__ import annotations

from pathlib import Path

import pytest

from govflow_backend.core.config import get_settings
from govflow_backend.rag.embeddings import FakeEmbeddingClient
from govflow_backend.rag.types import RagDocument
from govflow_backend.rag.vector_store.chroma import ChromaVectorStore


@pytest.fixture()
def chroma_store(tmp_path: Path) -> ChromaVectorStore:
    store = ChromaVectorStore(persist_directory=tmp_path / "ch", collection_name="unit")
    store.reset_collection()
    return store


def test_chroma_add_and_metadata_filter(chroma_store: ChromaVectorStore) -> None:
    settings = get_settings()
    emb = FakeEmbeddingClient(settings.rag_embedding_dimensions)
    docs = [
        RagDocument(doc_id="a", content="alpha uniquetermone", metadata={"source": "s1.md"}),
        RagDocument(doc_id="b", content="beta uniquetermtwo", metadata={"source": "s2.md"}),
    ]
    vectors = emb.embed_documents([d.content for d in docs])
    chroma_store.add_documents(documents=docs, embeddings=vectors)
    q = emb.embed_query("uniquetermtwo")
    hits = chroma_store.similarity_search(
        query_embedding=q,
        top_k=4,
        metadata_filter={"source": "s2.md"},
    )
    assert hits
    assert hits[0].metadata.get("source") == "s2.md"
