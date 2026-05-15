"""Vector store protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from govflow_backend.rag.schema import ScoredChunk
from govflow_backend.rag.types import RagDocument


@runtime_checkable
class VectorStore(Protocol):
    def add_documents(
        self, *, documents: list[RagDocument], embeddings: list[list[float]]
    ) -> int: ...

    def similarity_search(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        metadata_filter: dict[str, Any] | None,
    ) -> list[ScoredChunk]: ...

    def reset_collection(self) -> None: ...
