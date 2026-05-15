"""PostgreSQL + pgvector store (ready for production when `GOVFLOW_RAG_PG_DSN` is set)."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

from govflow_backend.exceptions import RagError
from govflow_backend.rag.schema import ScoredChunk
from govflow_backend.rag.types import RagDocument


class PgVectorVectorStore:
    """Cosine distance retrieval with JSONB metadata filtering (`@>` semantics)."""

    def __init__(self, *, dsn: str, collection_id: str, dimensions: int) -> None:
        if not dsn.strip():
            raise RagError("GOVFLOW_RAG_PG_DSN is empty for pgvector backend")
        self._dsn = dsn
        self._collection_id = collection_id
        self._dimensions = dimensions

    def _connect(self) -> psycopg.Connection:
        conn = psycopg.connect(self._dsn, autocommit=True)
        register_vector(conn)
        return conn

    def _ensure_schema(self, conn: psycopg.Connection) -> None:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS govflow_rag_vectors (
                id TEXT PRIMARY KEY,
                collection_id TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata JSONB NOT NULL,
                embedding vector({self._dimensions})
            )
            """,
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS govflow_rag_vectors_collection_idx "
            "ON govflow_rag_vectors (collection_id)",
        )

    def reset_collection(self) -> None:
        with self._connect() as conn:
            self._ensure_schema(conn)
            conn.execute(
                "DELETE FROM govflow_rag_vectors WHERE collection_id = %s", (self._collection_id,)
            )

    def add_documents(self, *, documents: list[RagDocument], embeddings: list[list[float]]) -> int:
        if len(documents) != len(embeddings):
            raise RagError("documents and embeddings length mismatch")
        if not documents:
            return 0
        with self._connect() as conn:
            self._ensure_schema(conn)
            with conn.cursor() as cur:
                for doc, emb in zip(documents, embeddings, strict=True):
                    vec = np.array(emb, dtype=np.float32)
                    cur.execute(
                        """
                        INSERT INTO govflow_rag_vectors (
                            id, collection_id, content, metadata, embedding
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding
                        """,
                        (
                            doc.doc_id,
                            self._collection_id,
                            doc.content,
                            json.dumps(doc.metadata),
                            vec,
                        ),
                    )
        return len(documents)

    def similarity_search(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        metadata_filter: dict[str, Any] | None,
    ) -> list[ScoredChunk]:
        qvec = np.array(query_embedding, dtype=np.float32)
        sql = """
            SELECT id, content, metadata, embedding <=> %(q)s::vector AS dist
            FROM govflow_rag_vectors
            WHERE collection_id = %(cid)s
        """
        bind: dict[str, Any] = {"q": qvec, "cid": self._collection_id, "k": top_k}
        if metadata_filter:
            sql += " AND metadata @> %(meta)s::jsonb"
            bind["meta"] = json.dumps(metadata_filter)
        sql += " ORDER BY dist ASC LIMIT %(k)s"

        with self._connect() as conn:
            self._ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(sql, bind)
                rows = cur.fetchall()
        chunks: list[ScoredChunk] = []
        for row in rows:
            cid, content, meta, dist = row
            score = 1.0 / (1.0 + float(dist or 0.0))
            chunks.append(
                ScoredChunk(
                    chunk_id=str(cid),
                    content=str(content),
                    score=score,
                    metadata=dict(meta) if isinstance(meta, dict) else {},
                ),
            )
        return chunks
