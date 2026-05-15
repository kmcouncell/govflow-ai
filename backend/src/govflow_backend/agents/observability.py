"""Collect token, latency, and estimated cost for an agent graph run."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from govflow_backend.agents.schema import AgentsPromptYaml, TelemetryLLMCall, TelemetryToolCall


@dataclass
class ObservabilityRun:
    """Mutable per-run collector (not stored in graph state)."""

    events: list[dict[str, Any]] = field(default_factory=list)

    def record_llm(
        self,
        *,
        agent: str,
        model: str | None,
        latency_s: float,
        input_tokens: int | None,
        output_tokens: int | None,
        total_tokens: int | None,
    ) -> None:
        event = TelemetryLLMCall(
            agent=agent,
            model=model,
            latency_ms=latency_s * 1000.0,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )
        self.events.append(event.model_dump())

    def record_tool(
        self,
        *,
        agent: str,
        tool_name: str,
        latency_s: float,
        attempts: int,
        ok: bool,
        error: str | None = None,
    ) -> None:
        event = TelemetryToolCall(
            agent=agent,
            tool_name=tool_name,
            latency_ms=latency_s * 1000.0,
            attempts=attempts,
            ok=ok,
            error=error,
        )
        self.events.append(event.model_dump())

    def summarize(self, pricing: AgentsPromptYaml) -> dict[str, Any]:
        total_latency_ms = sum(float(e.get("latency_ms") or 0.0) for e in self.events)
        input_tokens = 0
        output_tokens = 0
        for e in self.events:
            if e.get("kind") != "llm":
                continue
            it = e.get("input_tokens")
            ot = e.get("output_tokens")
            if it is not None:
                input_tokens += int(it)
            if ot is not None:
                output_tokens += int(ot)
        p_in = pricing.observability.price_per_million_input_tokens_usd
        p_out = pricing.observability.price_per_million_output_tokens_usd
        est_cost = (input_tokens / 1_000_000.0) * p_in + (output_tokens / 1_000_000.0) * p_out
        return {
            "events": list(self.events),
            "totals": {
                "latency_ms": total_latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": round(est_cost, 6),
            },
        }


class Stopwatch:
    def __init__(self) -> None:
        self._t0 = perf_counter()

    def seconds(self) -> float:
        return perf_counter() - self._t0
