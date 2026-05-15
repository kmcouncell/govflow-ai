"""Tool invocation helpers with retries and bounded backoff."""

from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any

from langchain_core.messages import ToolMessage

from govflow_backend.agents.observability import ObservabilityRun, Stopwatch
from govflow_backend.agents.schema import AgentsPromptYaml


async def invoke_tool_with_retries(
    *,
    tool: Any,
    tool_call_id: str,
    tool_name: str,
    tool_args: dict[str, Any],
    agent: str,
    prompts: AgentsPromptYaml,
    telemetry: ObservabilityRun,
) -> ToolMessage:
    """Invoke a LangChain tool with retries; always returns a ToolMessage."""

    retry = prompts.defaults.tool_retry
    attempt = 0
    last_error: str | None = None
    while attempt < retry.max_attempts:
        attempt += 1
        sw = Stopwatch()
        try:
            if inspect.iscoroutinefunction(tool.invoke):
                result = await tool.ainvoke(tool_args)
            else:
                result = await asyncio.to_thread(tool.invoke, tool_args)
            telemetry.record_tool(
                agent=agent,
                tool_name=tool_name,
                latency_s=sw.seconds(),
                attempts=attempt,
                ok=True,
            )
            if isinstance(result, str):
                content = result
            else:
                content = json.dumps(result, default=str)
            return ToolMessage(content=content, tool_call_id=tool_call_id, name=tool_name)
        except Exception as exc:  # noqa: BLE001 - tool boundary
            last_error = str(exc)
            telemetry.record_tool(
                agent=agent,
                tool_name=tool_name,
                latency_s=sw.seconds(),
                attempts=attempt,
                ok=False,
                error=last_error,
            )
            if attempt >= retry.max_attempts:
                break
            backoff = retry.initial_backoff_seconds * (retry.backoff_multiplier ** (attempt - 1))
            await asyncio.sleep(backoff)

    return ToolMessage(
        content=f"Tool {tool_name} failed after {attempt} attempt(s): {last_error}",
        tool_call_id=tool_call_id,
        name=tool_name,
    )
