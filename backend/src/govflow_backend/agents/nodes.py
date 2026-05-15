"""LangGraph node implementations for supervisor + specialists."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Literal

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.config import get_config

from govflow_backend.agents.builtin_tools import tools_for_agent
from govflow_backend.agents.observability import ObservabilityRun, Stopwatch
from govflow_backend.agents.schema import AgentsPromptYaml, SupervisorRoutingDecision
from govflow_backend.agents.state import AgentGraphState
from govflow_backend.agents.tooling import invoke_tool_with_retries
from govflow_backend.config_models import MergedFileConfig
from govflow_backend.core.config import GovFlowSettings
from govflow_backend.core.logging import get_logger

log = get_logger(__name__)


def _telemetry_from_runtime() -> ObservabilityRun:
    cfg = get_config() or {}
    conf = cfg.get("configurable") or {}
    tel = conf.get("telemetry")
    return tel if isinstance(tel, ObservabilityRun) else ObservabilityRun()


def _last_human_text(messages: Sequence[BaseMessage]) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            content = m.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts: list[str] = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(str(block.get("text", "")))
                return "\n".join(parts).strip()
            return str(content)
    return ""


def _degraded_route(
    messages: Sequence[BaseMessage],
) -> Literal["workflow_assistant", "research_agent", "document_analyzer", "FINISH"]:
    if not messages:
        return "workflow_assistant"
    last = messages[-1]
    if isinstance(last, AIMessage):
        return "FINISH"
    text = _last_human_text(messages).lower()
    if "research" in text:
        return "research_agent"
    if "document" in text or "analyze" in text or "pdf" in text:
        return "document_analyzer"
    return "workflow_assistant"


def _usage_from_message(msg: AIMessage) -> tuple[int | None, int | None, int | None]:
    meta = msg.usage_metadata
    if not meta:
        return None, None, None
    inp = meta.get("input_tokens")
    out = meta.get("output_tokens")
    tot = meta.get("total_tokens")
    return (
        int(inp) if inp is not None else None,
        int(out) if out is not None else None,
        int(tot) if tot is not None else None,
    )


def build_supervisor_node(
    *,
    settings: GovFlowSettings,
    file_config: MergedFileConfig,
    prompts: AgentsPromptYaml,
    chat_model: ChatOpenAI | None,
) -> Callable[[AgentGraphState], Awaitable[dict[str, Any]]]:
    async def supervisor_node(state: AgentGraphState) -> dict[str, Any]:
        telemetry = _telemetry_from_runtime()
        messages = state.get("messages") or []
        turns = int(state.get("supervisor_turns") or 0)
        if turns >= prompts.defaults.max_supervisor_turns:
            return {"supervisor_turns": 1, "last_route": "FINISH"}

        llm_ready = bool(
            file_config.features.llm_enabled and settings.openai_api_key and chat_model is not None,
        )

        if not llm_ready:
            nxt = _degraded_route(messages)
            log.info("supervisor_degraded_route", next=nxt, turns=turns)
            return {"supervisor_turns": 1, "last_route": nxt}

        assert chat_model is not None
        sys = SystemMessage(
            content=(
                f"{prompts.agents.supervisor.system_message.strip()}\n\n"
                f"{prompts.agents.supervisor.routing_instruction.strip()}"
            ),
        )
        sw = Stopwatch()
        structured = chat_model.with_structured_output(SupervisorRoutingDecision, include_raw=True)
        raw_result: Any = await structured.ainvoke([sys, *messages])
        latency = sw.seconds()

        decision: SupervisorRoutingDecision
        raw_ai: AIMessage | None = None
        if isinstance(raw_result, SupervisorRoutingDecision):
            decision = raw_result
        elif isinstance(raw_result, dict):
            parsed = raw_result.get("parsed")
            decision = (
                parsed
                if isinstance(parsed, SupervisorRoutingDecision)
                else SupervisorRoutingDecision(next="FINISH")
            )
            maybe_raw = raw_result.get("raw")
            raw_ai = maybe_raw if isinstance(maybe_raw, AIMessage) else None
        else:
            decision = SupervisorRoutingDecision(next="FINISH")

        inp, out, tot = _usage_from_message(raw_ai) if raw_ai is not None else (None, None, None)
        telemetry.record_llm(
            agent="supervisor",
            model=getattr(chat_model, "model_name", None),
            latency_s=latency,
            input_tokens=inp,
            output_tokens=out,
            total_tokens=tot,
        )
        log.info("supervisor_route", next=decision.next, rationale=decision.rationale)
        return {"supervisor_turns": 1, "last_route": decision.next}

    return supervisor_node


def _tool_map(tools: list[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for t in tools:
        name = getattr(t, "name", None)
        if name:
            out[str(name)] = t
    return out


def build_specialist_node(
    *,
    agent_key: Literal["workflow_assistant", "research_agent", "document_analyzer"],
    settings: GovFlowSettings,
    file_config: MergedFileConfig,
    prompts: AgentsPromptYaml,
    chat_model: ChatOpenAI | None,
) -> Callable[[AgentGraphState], Awaitable[dict[str, Any]]]:
    async def specialist_node(state: AgentGraphState) -> dict[str, Any]:
        telemetry = _telemetry_from_runtime()
        messages = list(state.get("messages") or [])

        if agent_key == "workflow_assistant":
            sys_text = prompts.agents.workflow_assistant.system_message
            degraded_text = prompts.agents.workflow_assistant.degraded_response
        elif agent_key == "research_agent":
            sys_text = prompts.agents.research_agent.system_message
            degraded_text = prompts.agents.research_agent.degraded_response
        else:
            sys_text = prompts.agents.document_analyzer.system_message
            degraded_text = prompts.agents.document_analyzer.degraded_response

        llm_ready = bool(
            file_config.features.llm_enabled and settings.openai_api_key and chat_model is not None,
        )
        if not llm_ready:
            return {
                "messages": [AIMessage(content=degraded_text.strip())],
                "last_active_agent": agent_key,
            }

        assert chat_model is not None

        tools = tools_for_agent(agent_key, prompts)
        tool_by_name = _tool_map(tools)
        model = chat_model.bind_tools(tools) if tools else chat_model

        sys = SystemMessage(content=sys_text.strip())
        working: list[AnyMessage] = [sys, *messages]
        max_iters = prompts.defaults.max_tool_iterations_per_specialist

        out_messages: list[AnyMessage] = []
        last_ai: AIMessage | None = None
        for _ in range(max_iters):
            sw = Stopwatch()
            ai_msg = await model.ainvoke(working)
            assert isinstance(ai_msg, AIMessage)
            last_ai = ai_msg
            out_messages.append(ai_msg)
            inp, out, tot = _usage_from_message(ai_msg)
            telemetry.record_llm(
                agent=agent_key,
                model=getattr(chat_model, "model_name", None),
                latency_s=sw.seconds(),
                input_tokens=inp,
                output_tokens=out,
                total_tokens=tot,
            )

            if not ai_msg.tool_calls:
                return {"messages": out_messages, "last_active_agent": agent_key}

            working.append(ai_msg)
            for call in ai_msg.tool_calls:
                name = str(call.get("name", ""))
                call_id = str(call.get("id", name))
                raw_args = call.get("args", {}) or {}
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args) if raw_args else {}
                    except json.JSONDecodeError:
                        args = {}
                elif isinstance(raw_args, dict):
                    args = raw_args
                else:
                    args = {}

                tool = tool_by_name.get(name)
                if tool is None:
                    tm = ToolMessage(
                        content=f"Unknown tool: {name}",
                        tool_call_id=call_id,
                        name=name,
                    )
                    out_messages.append(tm)
                    working.append(tm)
                    continue

                tm = await invoke_tool_with_retries(
                    tool=tool,
                    tool_call_id=call_id,
                    tool_name=name,
                    tool_args=args,
                    agent=agent_key,
                    prompts=prompts,
                    telemetry=telemetry,
                )
                out_messages.append(tm)
                working.append(tm)

        if last_ai is None:
            last_ai = AIMessage(content="[agent] No model output.")
            return {"messages": [last_ai], "last_active_agent": agent_key}
        return {"messages": out_messages, "last_active_agent": agent_key}

    return specialist_node
