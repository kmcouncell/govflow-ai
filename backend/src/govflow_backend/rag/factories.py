"""Construct embedding clients, vector stores, and the composed RAG runtime."""

from __future__ import annotations

from dataclasses import dataclass

from govflow_backend.core.config import GovFlowSettings
from govflow_backend.exceptions import ConfigurationError
from govflow_backend.rag.embeddings import EmbeddingClient, build_embedding_client
from govflow_backend.rag.ingestion import IngestionService
from govflow_backend.rag.qa import QaService
from govflow_backend.rag.retrieval import Retriever
from govflow_backend.rag.schema import RagYamlRoot
from govflow_backend.rag.vector_store.base import VectorStore
from govflow_backend.rag.vector_store.chroma import ChromaVectorStore
from govflow_backend.rag.vector_store.pgvector import PgVectorVectorStore


def build_vector_store(settings: GovFlowSettings) -> VectorStore:
    backend = settings.rag_vector_backend.strip().lower()
    if backend == "chroma":
        return ChromaVectorStore(
            persist_directory=settings.resolved_rag_chroma_dir,
            collection_name=settings.rag_collection_name,
        )
    if backend == "pgvector":
        return PgVectorVectorStore(
            dsn=settings.rag_pg_dsn,
            collection_id=settings.rag_collection_name,
            dimensions=settings.rag_embedding_dimensions,
        )
    raise ConfigurationError(
        f"Unsupported GOVFLOW_RAG_VECTOR_BACKEND: {settings.rag_vector_backend}"
    )


@dataclass(slots=True)
class RagRuntime:
    settings: GovFlowSettings
    rag_yaml: RagYamlRoot
    embedder: EmbeddingClient
    store: VectorStore
    ingestion: IngestionService
    retriever: Retriever
    qa: QaService


def build_rag_runtime(settings: GovFlowSettings, rag_yaml: RagYamlRoot) -> RagRuntime:
    prefer_fake = settings.rag_use_fake_embeddings or rag_yaml.embeddings.provider == "fake"
    embedder = build_embedding_client(settings, prefer_fake=prefer_fake)
    store = build_vector_store(settings)
    retriever = Retriever(embedder=embedder, store=store, rag_yaml=rag_yaml)
    ingestion = IngestionService(rag_yaml=rag_yaml, embedder=embedder, store=store)
    qa = QaService(settings=settings, rag_yaml=rag_yaml, retriever=retriever)
    return RagRuntime(
        settings=settings,
        rag_yaml=rag_yaml,
        embedder=embedder,
        store=store,
        ingestion=ingestion,
        retriever=retriever,
        qa=qa,
    )
