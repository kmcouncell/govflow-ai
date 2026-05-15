"""Pydantic models for agent prompt YAML and routing."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

AgentName = Literal["workflow_assistant", "research_agent", "document_analyzer"]
SupervisorRoute = Literal["workflow_assistant", "research_agent", "document_analyzer", "FINISH"]


class ToolRetryDefaults(BaseModel):
    max_attempts: int = Field(ge=1, le=20)
    initial_backoff_seconds: float = Field(ge=0.0, le=60.0)
    backoff_multiplier: float = Field(ge=1.0, le=10.0)


class DegradedRoutingConfig(BaseModel):
    """Keyword heuristics when the LLM path is unavailable (degraded supervisor)."""

    research_substrings: list[str] = Field(
        default_factory=lambda: ["research"],
        description="Substrings (case-insensitive); first match routes to research_agent.",
    )
    document_substrings: list[str] = Field(
        default_factory=lambda: ["document", "analyze", "pdf"],
        description="Case-insensitive substrings; evaluated after research_substrings.",
    )
    default_route: AgentName = Field(
        default="workflow_assistant",
        description="When no keyword matches, route to this specialist.",
    )


class AgentsDefaults(BaseModel):
    model_temperature: float = Field(ge=0.0, le=2.0)
    max_tool_iterations_per_specialist: int = Field(ge=1, le=50)
    max_supervisor_turns: int = Field(ge=1, le=100)
    tool_retry: ToolRetryDefaults
    degraded_routing: DegradedRoutingConfig = Field(default_factory=DegradedRoutingConfig)


class ObservabilityPricing(BaseModel):
    price_per_million_input_tokens_usd: float = Field(ge=0.0)
    price_per_million_output_tokens_usd: float = Field(ge=0.0)


class SupervisorAgentPrompts(BaseModel):
    system_message: str
    routing_instruction: str
    degraded_hint: str


class SpecialistAgentPrompts(BaseModel):
    system_message: str
    degraded_response: str
    enabled_tools: list[str] = Field(default_factory=list)


class AgentsPromptSection(BaseModel):
    supervisor: SupervisorAgentPrompts
    workflow_assistant: SpecialistAgentPrompts
    research_agent: SpecialistAgentPrompts
    document_analyzer: SpecialistAgentPrompts


class ToolSpecEntry(BaseModel):
    description: str


class AgentsPromptYaml(BaseModel):
    version: int = Field(ge=1)
    defaults: AgentsDefaults
    observability: ObservabilityPricing
    agents: AgentsPromptSection
    tool_specs: dict[str, ToolSpecEntry]


class SupervisorRoutingDecision(BaseModel):
    """Structured supervisor output when an LLM is available."""

    next: SupervisorRoute = Field(description="Next node to invoke, or FINISH.")
    rationale: str = Field(default="", description="Short internal rationale.")


class GraphInvokeMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None
    tool_call_id: str | None = None


class GraphInvokeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Summarize agency onboarding steps for a new hire.",
                        },
                    ],
                    "thread_id": "demo-thread-001",
                }
            ],
        },
    )

    messages: list[GraphInvokeMessage] = Field(
        default_factory=list,
        description="Conversation turns in LangChain-compatible roles.",
    )
    thread_id: str | None = Field(
        default=None,
        description="Optional stable thread identifier for client-side correlation.",
    )


class TelemetryLLMCall(BaseModel):
    kind: Literal["llm"] = "llm"
    agent: str
    model: str | None = None
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class TelemetryToolCall(BaseModel):
    kind: Literal["tool"] = "tool"
    agent: str
    tool_name: str
    latency_ms: float
    attempts: int
    ok: bool
    error: str | None = None


class GraphInvokeResponse(BaseModel):
    messages: list[dict[str, Any]]
    observability: dict[str, Any]
    active_agent: str | None = None
    guardrails: dict[str, Any] = Field(default_factory=dict)
    request_latency_ms: float | None = None
