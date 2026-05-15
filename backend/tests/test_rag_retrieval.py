from __future__ import annotations

from govflow_backend.core.config import get_settings
from govflow_backend.rag.embeddings import FakeEmbeddingClient
from govflow_backend.rag.factories import build_vector_store
from govflow_backend.rag.retrieval import Retriever
from govflow_backend.rag.types import RagDocument
from govflow_backend.rag.yaml_loader import load_rag_config


def test_retriever_respects_score_threshold() -> None:
    settings = get_settings()
    rag = load_rag_config(config_dir=settings.resolved_config_dir, environment=settings.environment)
    rag_strict = rag.model_copy(
        update={
            "retrieval": rag.retrieval.model_copy(update={"score_threshold": 1.01}),
        },
    )
    store = build_vector_store(settings)
    store.reset_collection()
    emb = FakeEmbeddingClient(settings.rag_embedding_dimensions)
    docs = [RagDocument(doc_id="only", content="thresholdtesttoken", metadata={"tag": "t"})]
    store.add_documents(documents=docs, embeddings=emb.embed_documents([d.content for d in docs]))

    retriever = Retriever(embedder=emb, store=store, rag_yaml=rag_strict)
    hits = retriever.retrieve(query="thresholdtesttoken", metadata_filter={"tag": "t"}, top_k=5)
    assert hits == []
