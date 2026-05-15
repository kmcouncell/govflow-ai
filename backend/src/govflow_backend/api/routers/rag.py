"""HTTP endpoints for ingestion and grounded QA."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter()


class IngestRequest(BaseModel):
    reset: bool = Field(
        default=False, description="If true, clears the configured vector collection first."
    )


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    metadata_filter: dict[str, Any] | None = Field(
        default=None,
        description="Equality filter on chunk metadata (Chroma/pgvector compatible JSON types).",
    )
    top_k: int | None = Field(default=None, ge=1, le=100)


@router.post("/ingest")
async def rag_ingest(request: Request, body: IngestRequest) -> dict[str, Any]:
    runtime = request.app.state.rag_runtime
    result = await asyncio.to_thread(lambda: runtime.ingestion.ingest(reset=body.reset))
    return {"documents_loaded": result.documents_loaded, "chunks_indexed": result.chunks_indexed}


@router.post("/query")
async def rag_query(request: Request, body: QueryRequest) -> dict[str, Any]:
    runtime = request.app.state.rag_runtime
    qa = await asyncio.to_thread(
        lambda: runtime.qa.answer(
            question=body.question,
            metadata_filter=body.metadata_filter,
            top_k=body.top_k,
        ),
    )
    return qa.model_dump()
