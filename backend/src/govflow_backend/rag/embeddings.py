"""Embedding clients (OpenAI + deterministic fake for tests)."""

from __future__ import annotations

import hashlib
from typing import Protocol, runtime_checkable

import numpy as np

from govflow_backend.core.config import GovFlowSettings
from govflow_backend.exceptions import RagError


@runtime_checkable
class EmbeddingClient(Protocol):
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class FakeEmbeddingClient:
    """Deterministic pseudo-embeddings (no network; dimension from settings)."""

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], "big", signed=False) % (2**32)
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(self.dimensions, dtype=np.float64)
        norm = float(np.linalg.norm(v)) + 1e-9
        return (v / norm).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class OpenAIEmbeddingClient:
    """OpenAI embeddings via LangChain (credentials from `GovFlowSettings`)."""

    def __init__(self, settings: GovFlowSettings) -> None:
        if not settings.openai_api_key:
            raise RagError("GOVFLOW_OPENAI_API_KEY is required for OpenAI embeddings")
        from langchain_openai import OpenAIEmbeddings

        kwargs: dict = {
            "model": settings.rag_embedding_model,
            "api_key": settings.openai_api_key,
        }
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        self._client = OpenAIEmbeddings(**kwargs)
        self.dimensions = int(settings.rag_embedding_dimensions)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._client.embed_query(text)


def build_embedding_client(settings: GovFlowSettings, *, prefer_fake: bool) -> EmbeddingClient:
    if settings.rag_use_fake_embeddings or prefer_fake:
        return FakeEmbeddingClient(settings.rag_embedding_dimensions)
    return OpenAIEmbeddingClient(settings)
