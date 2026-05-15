"""Minimal LangGraph workflow with graceful degradation when LLM is disabled."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph

from govflow_backend.config_models import MergedFileConfig
from govflow_backend.exceptions import ExternalServiceError
from govflow_backend.core.config import GovFlowSettings


class GraphState(TypedDict, total=False):
    messages: list[str]
    step_count: int


def _router_node(state: GraphState, *, settings: GovFlowSettings, file_config: MergedFileConfig) -> GraphState:
    if not file_config.features.llm_enabled or not settings.openai_api_key:
        return {
            "messages": (state.get("messages") or [])
            + ["LLM features are disabled or not configured; operating in degraded mode."],
            "step_count": int(state.get("step_count") or 0) + 1,
        }
    raise ExternalServiceError("LLM path is not implemented in this bootstrap graph.")


def build_stub_graph(settings: GovFlowSettings, file_config: MergedFileConfig):
    """Compile a small graph for health and future agent expansion."""

    graph = StateGraph(GraphState)

    def node(state: GraphState) -> GraphState:
        return _router_node(state, settings=settings, file_config=file_config)

    graph.add_node("agent", node)
    graph.set_entry_point("agent")
    graph.add_edge("agent", END)
    return graph.compile()
