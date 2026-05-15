"""Serialize and deserialize LangChain messages for HTTP APIs."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from govflow_backend.agents.schema import GraphInvokeMessage


def messages_from_request(items: list[GraphInvokeMessage]) -> list[AnyMessage]:
    out: list[AnyMessage] = []
    for m in items:
        if m.role == "system":
            out.append(SystemMessage(content=m.content, name=m.name))
        elif m.role == "user":
            out.append(HumanMessage(content=m.content, name=m.name))
        elif m.role == "assistant":
            out.append(AIMessage(content=m.content, name=m.name))
        elif m.role == "tool":
            out.append(
                ToolMessage(
                    content=m.content,
                    name=m.name or "tool",
                    tool_call_id=m.tool_call_id or m.name or "tool",
                ),
            )
    return out


def messages_to_jsonable(messages: list[BaseMessage]) -> list[dict[str, Any]]:
    return [m.model_dump(mode="json") for m in messages]
