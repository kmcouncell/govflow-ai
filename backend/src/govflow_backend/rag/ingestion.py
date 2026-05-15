"""Orchestrate load → chunk → embed → index."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document

from govflow_backend.rag.chunking import build_recursive_splitter, split_rag_documents
from govflow_backend.rag.embeddings import EmbeddingClient
from govflow_backend.rag.loaders import load_raw_documents
from govflow_backend.rag.schema import RagYamlRoot
from govflow_backend.rag.types import RagDocument
from govflow_backend.rag.vector_store.base import VectorStore


@dataclass(slots=True)
class IngestionResult:
    documents_loaded: int
    chunks_indexed: int


class IngestionService:
    def __init__(
        self,
        *,
        rag_yaml: RagYamlRoot,
        embedder: EmbeddingClient,
        store: VectorStore,
    ) -> None:
        self._rag_yaml = rag_yaml
        self._embedder = embedder
        self._store = store

    def ingest(self, *, reset: bool) -> IngestionResult:
        if reset:
            self._store.reset_collection()

        raw = load_raw_documents(self._rag_yaml.ingestion)
        lc_docs = [
            Document(page_content=d.content, metadata={**d.metadata, "parent_doc_id": d.doc_id})
            for d in raw
        ]
        splitter = build_recursive_splitter(self._rag_yaml.chunking)
        split_docs = split_rag_documents(documents=lc_docs, splitter=splitter)

        chunks: list[RagDocument] = []
        for idx, doc in enumerate(split_docs):
            parent = str(doc.metadata.get("parent_doc_id", "unknown"))
            cid = f"{parent}::chunk::{idx}"
            meta = {k: v for k, v in doc.metadata.items() if k != "parent_doc_id"}
            meta["parent_doc_id"] = parent
            meta["chunk_index"] = idx
            chunks.append(RagDocument(doc_id=cid, content=doc.page_content, metadata=meta))

        if not chunks:
            return IngestionResult(documents_loaded=len(raw), chunks_indexed=0)

        vectors = self._embedder.embed_documents([c.content for c in chunks])
        written = self._store.add_documents(documents=chunks, embeddings=vectors)
        return IngestionResult(documents_loaded=len(raw), chunks_indexed=written)
