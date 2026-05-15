"""LangGraph agent routes (invoke + streaming)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage

from govflow_backend.agents.messages import messages_from_request, messages_to_jsonable
from govflow_backend.agents.observability import ObservabilityRun
from govflow_backend.agents.schema import GraphInvokeRequest, GraphInvokeResponse
from govflow_backend.core.logging import get_logger
from govflow_backend.exceptions import ConfigurationError, GuardrailsError
from govflow_backend.observability.audit import log_ai_audit
from govflow_backend.responsible_ai.guardrails import (
    GuardrailTextOutcome,
    apply_guardrails_to_assistant_messages,
    apply_text_guardrails,
    validate_user_input_text,
)
from govflow_backend.responsible_ai.schema import ResponsibleAiYaml

router = APIRouter()
log = get_logger(__name__)


def _json_default(value: object) -> object:
    if isinstance(value, BaseMessage):
        return value.model_dump(mode="json")
    return str(value)


def _ra(request: Request) -> ResponsibleAiYaml:
    ra = request.app.state.responsible_ai
    if not isinstance(ra, ResponsibleAiYaml):
        raise ConfigurationError("Responsible AI configuration is not loaded on the application.")
    return ra


def _user_text_from_invoke(body: GraphInvokeRequest) -> str:
    return "\n".join(m.content for m in body.messages if m.role == "user")


def _validate_invoke_input(request: Request, body: GraphInvokeRequest) -> None:
    ra = _ra(request)
    text = _user_text_from_invoke(body)
    if not text.strip():
        return
    res = validate_user_input_text(text, ra.guardrails)
    if res.blocked:
        raise GuardrailsError(res.block_reason or "Input blocked by guardrails.", flags=res.flags)


def _assistant_texts_from_chunk(chunk: dict[str, Any]) -> list[str]:
    acc: list[str] = []
    for v in chunk.values():
        _walk_for_ai_content(v, acc)
    return acc


def _walk_for_ai_content(obj: Any, acc: list[str]) -> None:
    if isinstance(obj, AIMessage):
        ai_content = obj.content
        if isinstance(ai_content, str):
            acc.append(ai_content)
        return
    if isinstance(obj, dict):
        if obj.get("type") == "ai":
            dc = obj.get("content")
            if isinstance(dc, str):
                acc.append(dc)
        for vv in obj.values():
            _walk_for_ai_content(vv, acc)
    elif isinstance(obj, (list, tuple)):
        for it in obj:
            _walk_for_ai_content(it, acc)


@router.post("/demo", summary="Run supervisor graph (degraded when LLM is off)")
async def graph_demo(request: Request) -> dict[str, Any]:
    t0 = perf_counter()
    ra = _ra(request)
    graph = request.app.state.graph
    prompts = request.app.state.agents_prompts
    telemetry = ObservabilityRun()
    file_config = request.app.state.file_config
    result = await graph.ainvoke(
        {"messages": [], "supervisor_turns": 0},
        config={
            "configurable": {"telemetry": telemetry},
            "recursion_limit": file_config.app.graph.max_steps,
        },
    )
    obs = telemetry.summarize(prompts)
    raw_messages = messages_to_jsonable(result.get("messages") or [])
    checked, gr_summary = apply_guardrails_to_assistant_messages(raw_messages, ra.guardrails)
    if gr_summary.get("blocked"):
        raise GuardrailsError(
            str(gr_summary.get("block_reason") or "Output blocked by guardrails."),
            flags=list(gr_summary.get("flags") or []),
        )
    elapsed_ms = (perf_counter() - t0) * 1000.0
    out_text = "\n".join(
        str(m.get("content", "")) for m in checked if isinstance(m, dict) and m.get("type") == "ai"
    )
    log_ai_audit(
        request=request,
        action="graph.demo",
        duration_ms=elapsed_ms,
        ra=ra,
        guardrails=gr_summary,
        blocked=False,
        observability=obs,
        input_text="",
        output_text=out_text,
    )
    return {
        "result": {
            "messages": checked,
            "observability": obs,
            "last_route": result.get("last_route"),
            "last_active_agent": result.get("last_active_agent"),
            "guardrails": gr_summary,
            "request_latency_ms": elapsed_ms,
        },
    }


@router.post("/invoke", summary="Invoke supervisor graph with messages")
async def graph_invoke(request: Request, body: GraphInvokeRequest) -> GraphInvokeResponse:
    t0 = perf_counter()
    ra = _ra(request)
    _validate_invoke_input(request, body)

    graph = request.app.state.graph
    prompts = request.app.state.agents_prompts
    telemetry = ObservabilityRun()
    file_config = request.app.state.file_config
    state: dict[str, Any] = {
        "messages": messages_from_request(body.messages),
        "supervisor_turns": 0,
    }
    out = await graph.ainvoke(
        state,
        config={
            "configurable": {"telemetry": telemetry},
            "recursion_limit": file_config.app.graph.max_steps,
        },
    )
    obs = telemetry.summarize(prompts)
    raw_messages = messages_to_jsonable(out.get("messages") or [])
    checked, gr_summary = apply_guardrails_to_assistant_messages(raw_messages, ra.guardrails)
    if gr_summary.get("blocked"):
        raise GuardrailsError(
            str(gr_summary.get("block_reason") or "Output blocked by guardrails."),
            flags=list(gr_summary.get("flags") or []),
        )
    elapsed_ms = (perf_counter() - t0) * 1000.0
    out_text = "\n".join(
        str(m.get("content", "")) for m in checked if isinstance(m, dict) and m.get("type") == "ai"
    )
    log_ai_audit(
        request=request,
        action="graph.invoke",
        duration_ms=elapsed_ms,
        ra=ra,
        guardrails=gr_summary,
        blocked=False,
        observability=obs,
        input_text=_user_text_from_invoke(body),
        output_text=out_text,
    )
    return GraphInvokeResponse(
        messages=checked,
        observability=obs,
        active_agent=out.get("last_active_agent"),
        guardrails=gr_summary,
        request_latency_ms=elapsed_ms,
    )


async def _stream_updates(
    *,
    graph: Any,
    state: dict[str, Any],
    config: dict[str, Any],
    prompts: Any,
    telemetry: ObservabilityRun,
    request: Request,
    ra: ResponsibleAiYaml,
    user_input: str,
) -> AsyncIterator[str]:
    t0 = perf_counter()
    assistant_parts: list[str] = []
    try:
        async for chunk in graph.astream(state, config=config, stream_mode="updates"):
            assistant_parts.extend(_assistant_texts_from_chunk(chunk))
            payload = json.dumps({"updates": chunk}, default=_json_default)
            yield f"data: {payload}\n\n"
    finally:
        summary = telemetry.summarize(prompts)
        joined = "\n".join(assistant_parts)
        stream_gr: dict[str, Any]
        if joined.strip():
            gout = apply_text_guardrails(joined, ra.guardrails)
            stream_gr = {**gout.as_dict(), "stream_aggregate": True}
        else:
            stream_gr = {**GuardrailTextOutcome("", []).as_dict(), "stream_aggregate": True}
        done_payload = json.dumps(
            {"done": True, "observability": summary, "guardrails": stream_gr},
            default=_json_default,
        )
        yield f"data: {done_payload}\n\n"
        elapsed_ms = (perf_counter() - t0) * 1000.0
        log_ai_audit(
            request=request,
            action="graph.stream",
            duration_ms=elapsed_ms,
            ra=ra,
            guardrails=stream_gr,
            blocked=bool(stream_gr.get("blocked")),
            observability=summary,
            input_text=user_input,
            output_text=joined,
        )


@router.post("/stream", summary="Stream graph node updates (SSE)")
async def graph_stream(request: Request, body: GraphInvokeRequest) -> StreamingResponse:
    ra = _ra(request)
    _validate_invoke_input(request, body)

    graph = request.app.state.graph
    prompts = request.app.state.agents_prompts
    telemetry = ObservabilityRun()
    file_config = request.app.state.file_config
    state = {"messages": messages_from_request(body.messages), "supervisor_turns": 0}
    config = {
        "configurable": {"telemetry": telemetry},
        "recursion_limit": file_config.app.graph.max_steps,
    }
    log.info("graph_stream_start", thread_id=body.thread_id)
    user_input = _user_text_from_invoke(body)
    stream = _stream_updates(
        graph=graph,
        state=state,
        config=config,
        prompts=prompts,
        telemetry=telemetry,
        request=request,
        ra=ra,
        user_input=user_input,
    )
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
