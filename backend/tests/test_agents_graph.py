from __future__ import annotations

from pathlib import Path

from langchain_core.messages import HumanMessage

from govflow_backend.agents.graph import build_supervisor_graph
from govflow_backend.agents.loader import load_agents_prompt_config
from govflow_backend.agents.observability import ObservabilityRun
from govflow_backend.config_loader import load_merged_file_config
from govflow_backend.config_models import MergedFileConfig
from govflow_backend.core.config import GovFlowSettings, get_settings


def _settings_and_config() -> tuple[GovFlowSettings, MergedFileConfig]:
    settings = get_settings()
    file_config = load_merged_file_config(
        config_dir=settings.resolved_config_dir,
        environment=settings.environment,
    )
    return settings, file_config


async def test_supervisor_routes_research_degraded() -> None:
    settings, file_config = _settings_and_config()
    repo = Path(__file__).resolve().parents[2]
    prompts = load_agents_prompt_config(
        config_dir=repo / "config",
        environment=settings.environment,
    )
    graph = build_supervisor_graph(settings, file_config, prompts)
    tel = ObservabilityRun()
    out = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="Please research procurement rules.")],
            "supervisor_turns": 0,
        },
        config={
            "configurable": {"telemetry": tel},
            "recursion_limit": file_config.app.graph.max_steps,
        },
    )
    msgs = out.get("messages") or []
    assert msgs
    last = msgs[-1]
    assert "ResearchAgent" in last.content or "research" in last.content.lower()


async def test_supervisor_finishes_after_specialist_degraded() -> None:
    settings, file_config = _settings_and_config()
    repo = Path(__file__).resolve().parents[2]
    prompts = load_agents_prompt_config(
        config_dir=repo / "config",
        environment=settings.environment,
    )
    graph = build_supervisor_graph(settings, file_config, prompts)
    tel = ObservabilityRun()
    out = await graph.ainvoke(
        {"messages": [], "supervisor_turns": 0},
        config={
            "configurable": {"telemetry": tel},
            "recursion_limit": file_config.app.graph.max_steps,
        },
    )
    summary = tel.summarize(prompts)
    assert "totals" in summary
    assert out.get("last_route") in (None, "FINISH")
