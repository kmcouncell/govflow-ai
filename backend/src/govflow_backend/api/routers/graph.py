"""LangGraph demo routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/demo", summary="Run stub graph (degraded when LLM is off)")
async def graph_demo(request: Request) -> dict[str, Any]:
    graph = request.app.state.graph
    result = await graph.ainvoke({"messages": [], "step_count": 0})
    return {"result": result}
