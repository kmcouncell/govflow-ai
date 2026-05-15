from __future__ import annotations

from pathlib import Path

from govflow_backend.agents.loader import load_agents_prompt_config


def test_load_agents_prompt_config_merges_development_overlay() -> None:
    repo = Path(__file__).resolve().parents[2]
    cfg = load_agents_prompt_config(config_dir=repo / "config", environment="development")
    assert cfg.version >= 1
    assert cfg.agents.supervisor.system_message
    assert cfg.defaults.max_supervisor_turns == 10
    assert "echo" in cfg.tool_specs


def test_tool_specs_cover_enabled_tools() -> None:
    repo = Path(__file__).resolve().parents[2]
    cfg = load_agents_prompt_config(config_dir=repo / "config", environment="development")
    for name in cfg.agents.workflow_assistant.enabled_tools:
        assert name in cfg.tool_specs
