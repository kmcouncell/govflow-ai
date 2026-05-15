"""Built-in LangChain tools; descriptions augmented from YAML `tool_specs`."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from langchain_core.tools import tool

from govflow_backend.agents.schema import AgentsPromptYaml


@tool
def echo(text: str) -> str:
    """Echo input for debugging and tracing tool execution."""

    return text


@tool
def current_time() -> str:
    """Return the current UTC time in ISO-8601 format."""

    return datetime.now(tz=UTC).isoformat()


@tool
def summarize_url_stub(url: str) -> str:
    """Stub summarizer for a URL (no outbound network); returns a placeholder summary."""

    return f"[stub summary for {url}] No live fetch in this environment."


@tool
def extract_key_points_stub(text: str) -> str:
    """Stub extractor that returns bullet key points from provided text."""

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    bullets = "\n".join(f"- {ln[:200]}" for ln in lines[:8])
    return bullets or "- (empty text)"


_TOOL_REGISTRY: dict[str, Any] = {
    "echo": echo,
    "current_time": current_time,
    "summarize_url_stub": summarize_url_stub,
    "extract_key_points_stub": extract_key_points_stub,
}


def tools_for_agent(agent_key: str, prompts: AgentsPromptYaml) -> list[Any]:
    spec = prompts.agents
    enabled: list[str]
    if agent_key == "workflow_assistant":
        enabled = spec.workflow_assistant.enabled_tools
    elif agent_key == "research_agent":
        enabled = spec.research_agent.enabled_tools
    elif agent_key == "document_analyzer":
        enabled = spec.document_analyzer.enabled_tools
    else:
        enabled = []

    tools: list[Any] = []
    for name in enabled:
        base = _TOOL_REGISTRY.get(name)
        if base is None:
            continue
        if name not in prompts.tool_specs:
            continue
        tools.append(base)
    return tools
