"""ChromaDB vector store implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb

from govflow_backend.exceptions import RagError
from govflow_backend.rag.schema import ScoredChunk
from govflow_backend.rag.types import RagDocument


def _flatten_metadata(meta: dict[str, Any]) -> dict[str, str | int | float | bool]:
    out: dict[str, str | int | float | bool] = {}
    for key, value in meta.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            out[key] = value
        else:
            out[key] = json.dumps(value, sort_keys=True)
    return out


def _chroma_where(metadata_filter: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata_filter:
        return None
    parts: list[dict[str, Any]] = []
    for key, value in metadata_filter.items():
        if isinstance(value, (str, int, float, bool)):
            parts.append({key: {"$eq": value}})
        else:
            parts.append({key: {"$eq": json.dumps(value, sort_keys=True)}})
    if len(parts) == 1:
        return parts[0]
    return {"$and": parts}


class ChromaVectorStore:
    """Persistent Chroma collection with cosine space."""

    def __init__(self, *, persist_directory: Path, collection_name: str) -> None:
        persist_directory.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_directory))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset_collection(self) -> None:
        name = self._collection.name
        self._client.delete_collection(name)
        self._collection = self._client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, *, documents: list[RagDocument], embeddings: list[list[float]]) -> int:
        if len(documents) != len(embeddings):
            raise RagError("documents and embeddings length mismatch")
        if not documents:
            return 0
        ids = [d.doc_id for d in documents]
        docs = [d.content for d in documents]
        metadatas = [_flatten_metadata(d.metadata) for d in documents]
        self._collection.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metadatas)
        return len(documents)

    def similarity_search(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        metadata_filter: dict[str, Any] | None,
    ) -> list[ScoredChunk]:
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=_chroma_where(metadata_filter),
            include=["documents", "distances", "metadatas"],
        )
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        chunks: list[ScoredChunk] = []
        for idx, cid in enumerate(ids):
            dist = float(distances[idx]) if idx < len(distances) else 1.0
            score = 1.0 / (1.0 + max(dist, 0.0))
            meta_raw = metadatas[idx] if idx < len(metadatas) else {}
            meta = dict(meta_raw or {})
            content = documents[idx] if idx < len(documents) else ""
            chunks.append(ScoredChunk(chunk_id=cid, content=content, score=score, metadata=meta))
        return chunks
