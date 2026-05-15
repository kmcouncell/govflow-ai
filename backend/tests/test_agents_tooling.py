from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from govflow_backend.agents.observability import ObservabilityRun
from govflow_backend.agents.schema import (
    AgentsDefaults,
    AgentsPromptSection,
    AgentsPromptYaml,
    ObservabilityPricing,
    SpecialistAgentPrompts,
    SupervisorAgentPrompts,
    ToolRetryDefaults,
    ToolSpecEntry,
)
from govflow_backend.agents.tooling import invoke_tool_with_retries


def _minimal_prompts() -> AgentsPromptYaml:
    sup = SupervisorAgentPrompts(system_message="s", routing_instruction="r", degraded_hint="h")
    sp = SpecialistAgentPrompts(system_message="a", degraded_response="d", enabled_tools=[])
    section = AgentsPromptSection(
        supervisor=sup,
        workflow_assistant=sp,
        research_agent=sp,
        document_analyzer=sp,
    )
    return AgentsPromptYaml(
        version=1,
        defaults=AgentsDefaults(
            model_temperature=0.1,
            max_tool_iterations_per_specialist=2,
            max_supervisor_turns=4,
            tool_retry=ToolRetryDefaults(
                max_attempts=3,
                initial_backoff_seconds=0.01,
                backoff_multiplier=2.0,
            ),
        ),
        observability=ObservabilityPricing(
            price_per_million_input_tokens_usd=1.0,
            price_per_million_output_tokens_usd=2.0,
        ),
        agents=section,
        tool_specs={"echo": ToolSpecEntry(description="x")},
    )


@pytest.mark.asyncio
async def test_tool_retries_then_success() -> None:
    tool = MagicMock()
    tool.invoke.side_effect = [RuntimeError("fail once"), "ok"]
    prompts = _minimal_prompts()
    tel = ObservabilityRun()
    msg = await invoke_tool_with_retries(
        tool=tool,
        tool_call_id="1",
        tool_name="echo",
        tool_args={"text": "hi"},
        agent="workflow_assistant",
        prompts=prompts,
        telemetry=tel,
    )
    assert "ok" in msg.content
    assert tool.invoke.call_count == 2


@pytest.mark.asyncio
async def test_tool_retries_exhausted() -> None:
    tool = MagicMock()
    tool.invoke.side_effect = RuntimeError("always fail")
    prompts = _minimal_prompts()
    prompts.defaults.tool_retry.max_attempts = 2
    prompts.defaults.tool_retry.initial_backoff_seconds = 0.01
    tel = ObservabilityRun()
    msg = await invoke_tool_with_retries(
        tool=tool,
        tool_call_id="1",
        tool_name="echo",
        tool_args={"text": "hi"},
        agent="workflow_assistant",
        prompts=prompts,
        telemetry=tel,
    )
    assert "failed" in msg.content.lower()
    assert tool.invoke.call_count == 2
