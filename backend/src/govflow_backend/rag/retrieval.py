"""Retrieval with optional metadata filters."""

from __future__ import annotations

from typing import Any

from govflow_backend.rag.embeddings import EmbeddingClient
from govflow_backend.rag.schema import RagYamlRoot, ScoredChunk
from govflow_backend.rag.vector_store.base import VectorStore


class Retriever:
    def __init__(
        self, *, embedder: EmbeddingClient, store: VectorStore, rag_yaml: RagYamlRoot
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._rag_yaml = rag_yaml

    def retrieve(
        self,
        *,
        query: str,
        metadata_filter: dict[str, Any] | None,
        top_k: int | None,
    ) -> list[ScoredChunk]:
        k = top_k if top_k is not None else self._rag_yaml.retrieval.default_top_k
        embedding = self._embedder.embed_query(query)
        chunks = self._store.similarity_search(
            query_embedding=embedding,
            top_k=k,
            metadata_filter=metadata_filter,
        )
        threshold = self._rag_yaml.retrieval.score_threshold
        if threshold is not None:
            chunks = [c for c in chunks if c.score >= threshold]
        return chunks
