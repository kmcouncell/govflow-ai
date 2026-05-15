"""LangGraph state definitions with Pydantic mirrors for API snapshots."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


def _add_int(left: int, right: int) -> int:
    return int(left) + int(right)


class AgentGraphState(TypedDict, total=False):
    """Runtime graph state (TypedDict for LangGraph reducers)."""

    messages: Annotated[list[AnyMessage], add_messages]
    supervisor_turns: Annotated[int, _add_int]
    last_route: str
    last_active_agent: str


class AgentGraphStateModel(BaseModel):
    """Pydantic snapshot of graph state for tests and API serialization."""

    messages: list[dict[str, Any]] = Field(default_factory=list)
    supervisor_turns: int = 0
    last_route: str | None = None
    last_active_agent: str | None = None
