"""Compile the supervisor LangGraph."""

from __future__ import annotations

from typing import Any, Literal, cast

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from govflow_backend.agents.nodes import build_specialist_node, build_supervisor_node
from govflow_backend.agents.schema import AgentsPromptYaml
from govflow_backend.agents.state import AgentGraphState
from govflow_backend.config_models import MergedFileConfig
from govflow_backend.core.config import GovFlowSettings

SPECIALIST_KEYS: tuple[
    Literal["workflow_assistant", "research_agent", "document_analyzer"],
    ...,
] = ("workflow_assistant", "research_agent", "document_analyzer")


def _make_chat_model(settings: GovFlowSettings, prompts: AgentsPromptYaml) -> ChatOpenAI | None:
    if not settings.openai_api_key:
        return None
    model_name = settings.openai_model or "gpt-4o-mini"
    kwargs: dict[str, Any] = {
        "model": model_name,
        "api_key": settings.openai_api_key,
        "temperature": prompts.defaults.model_temperature,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)


def _route_after_supervisor(state: AgentGraphState) -> object:
    route = state.get("last_route")
    if route in ("workflow_assistant", "research_agent", "document_analyzer"):
        return route
    return END


def build_supervisor_graph(
    settings: GovFlowSettings,
    file_config: MergedFileConfig,
    agents_prompts: AgentsPromptYaml,
) -> Any:
    chat_model: ChatOpenAI | None = None
    if file_config.features.llm_enabled and settings.openai_api_key:
        chat_model = _make_chat_model(settings, agents_prompts)

    graph = StateGraph(AgentGraphState)
    graph.add_node(
        "supervisor",
        cast(Any, build_supervisor_node(
            settings=settings,
            file_config=file_config,
            prompts=agents_prompts,
            chat_model=chat_model,
        )),
    )
    for key in SPECIALIST_KEYS:
        graph.add_node(
            key,
            cast(
                Any,
                build_specialist_node(
                    agent_key=key,
                    settings=settings,
                    file_config=file_config,
                    prompts=agents_prompts,
                    chat_model=chat_model,
                ),
            ),
        )

    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "workflow_assistant": "workflow_assistant",
            "research_agent": "research_agent",
            "document_analyzer": "document_analyzer",
            END: END,
        },
    )
    graph.add_edge("workflow_assistant", "supervisor")
    graph.add_edge("research_agent", "supervisor")
    graph.add_edge("document_analyzer", "supervisor")
    return graph.compile()
