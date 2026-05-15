"""LangGraph agent routes (invoke + streaming)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import BaseMessage

from govflow_backend.agents.messages import messages_from_request, messages_to_jsonable
from govflow_backend.agents.observability import ObservabilityRun
from govflow_backend.agents.schema import GraphInvokeRequest, GraphInvokeResponse
from govflow_backend.core.logging import get_logger

router = APIRouter()
log = get_logger(__name__)


def _json_default(value: object) -> object:
    if isinstance(value, BaseMessage):
        return value.model_dump(mode="json")
    return str(value)


@router.post("/demo", summary="Run supervisor graph (degraded when LLM is off)")
async def graph_demo(request: Request) -> dict[str, Any]:
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
    return {
        "result": {
            "messages": messages_to_jsonable(result.get("messages") or []),
            "observability": obs,
            "last_route": result.get("last_route"),
            "last_active_agent": result.get("last_active_agent"),
        },
    }


@router.post("/invoke", summary="Invoke supervisor graph with messages")
async def graph_invoke(request: Request, body: GraphInvokeRequest) -> GraphInvokeResponse:
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
    return GraphInvokeResponse(
        messages=messages_to_jsonable(out.get("messages") or []),
        observability=obs,
        active_agent=out.get("last_active_agent"),
    )


async def _stream_updates(
    *,
    graph: Any,
    state: dict[str, Any],
    config: dict[str, Any],
    prompts: Any,
    telemetry: ObservabilityRun,
) -> AsyncIterator[str]:
    try:
        async for chunk in graph.astream(state, config=config, stream_mode="updates"):
            payload = json.dumps({"updates": chunk}, default=_json_default)
            yield f"data: {payload}\n\n"
    finally:
        summary = telemetry.summarize(prompts)
        done_payload = json.dumps(
            {"done": True, "observability": summary},
            default=_json_default,
        )
        yield f"data: {done_payload}\n\n"


@router.post("/stream", summary="Stream graph node updates (SSE)")
async def graph_stream(request: Request, body: GraphInvokeRequest) -> StreamingResponse:
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
    stream = _stream_updates(
        graph=graph,
        state=state,
        config=config,
        prompts=prompts,
        telemetry=telemetry,
    )
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
