"""HTTP endpoints for ingestion and grounded QA."""

from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from govflow_backend.exceptions import ConfigurationError, GuardrailsError
from govflow_backend.observability.audit import log_ai_audit
from govflow_backend.responsible_ai.guardrails import (
    apply_text_guardrails,
    validate_user_input_text,
)
from govflow_backend.responsible_ai.schema import ResponsibleAiYaml

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


def _ra(request: Request) -> ResponsibleAiYaml:
    ra = request.app.state.responsible_ai
    if not isinstance(ra, ResponsibleAiYaml):
        raise ConfigurationError("Responsible AI configuration is not loaded on the application.")
    return ra


@router.post("/ingest")
async def rag_ingest(request: Request, body: IngestRequest) -> dict[str, Any]:
    t0 = perf_counter()
    ra = _ra(request)
    runtime = request.app.state.rag_runtime
    result = await asyncio.to_thread(lambda: runtime.ingestion.ingest(reset=body.reset))
    elapsed_ms = (perf_counter() - t0) * 1000.0
    log_ai_audit(
        request=request,
        action="rag.ingest",
        duration_ms=elapsed_ms,
        ra=ra,
        guardrails={"flags": [], "blocked": False},
        blocked=False,
        input_text=f"reset={body.reset}",
        output_text=f"documents_loaded={result.documents_loaded},chunks_indexed={result.chunks_indexed}",
    )
    return {"documents_loaded": result.documents_loaded, "chunks_indexed": result.chunks_indexed}


@router.post("/query")
async def rag_query(request: Request, body: QueryRequest) -> dict[str, Any]:
    t0 = perf_counter()
    ra = _ra(request)
    iv = validate_user_input_text(body.question, ra.guardrails)
    if iv.blocked:
        raise GuardrailsError(iv.block_reason or "Question blocked by guardrails.", flags=iv.flags)

    runtime = request.app.state.rag_runtime
    qa = await asyncio.to_thread(
        lambda: runtime.qa.answer(
            question=body.question,
            metadata_filter=body.metadata_filter,
            top_k=body.top_k,
        ),
    )
    payload = qa.model_dump()
    answer = str(payload.get("answer", ""))
    gr = apply_text_guardrails(answer, ra.guardrails)
    if gr.blocked:
        raise GuardrailsError(gr.block_reason or "Answer blocked by guardrails.", flags=gr.flags)
    payload["answer"] = gr.text
    payload["guardrails"] = gr.as_dict()
    payload["request_latency_ms"] = (perf_counter() - t0) * 1000.0
    log_ai_audit(
        request=request,
        action="rag.query",
        duration_ms=float(payload["request_latency_ms"]),
        ra=ra,
        guardrails=gr.as_dict(),
        blocked=False,
        input_text=body.question,
        output_text=gr.text,
    )
    return dict(payload)
