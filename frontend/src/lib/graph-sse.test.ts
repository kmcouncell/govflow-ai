import { describe, expect, it } from "vitest";

import {
  extractAssistantTextFromSsePayload,
  extractThoughtLinesFromSsePayload,
  formatObservabilityForThoughtPanel,
  parseSseDataLine,
} from "@/lib/graph-sse";

describe("graph-sse", () => {
  it("extracts assistant text from LangChain-style AI message objects", () => {
    const text = extractAssistantTextFromSsePayload({
      updates: { step: { messages: [{ type: "ai", content: "Hello from graph" }] } },
    });
    expect(text).toBe("Hello from graph");
  });

  it("extracts routing thought lines from supervisor updates", () => {
    const lines = extractThoughtLinesFromSsePayload({
      updates: { supervisor: { last_route: "workflow_assistant", supervisor_turns: 1 } },
    });
    expect(lines.some((l) => l.includes("workflow_assistant"))).toBe(true);
  });

  it("formats observability totals and events", () => {
    const lines = formatObservabilityForThoughtPanel({
      totals: { latency_ms: 12.3, input_tokens: 1, output_tokens: 2, estimated_cost_usd: 0.000001 },
      events: [
        { kind: "llm", agent: "supervisor", latency_ms: 10 },
        { kind: "tool", agent: "research_agent", tool_name: "search", ok: true },
      ],
    });
    expect(lines.some((l) => l.includes("LLM"))).toBe(true);
    expect(lines.some((l) => l.includes("Tool"))).toBe(true);
  });

  it("parses done events", () => {
    const ev = parseSseDataLine(JSON.stringify({ done: true }));
    expect(ev?.kind).toBe("done");
  });

  it("parses update events with assistant delta and thought lines", () => {
    const ev = parseSseDataLine(
      JSON.stringify({
        updates: {
          supervisor: { last_route: "research_agent" },
          research_agent: { messages: [{ type: "ai", content: "Hi" }] },
        },
      }),
    );
    expect(ev?.kind).toBe("update");
    if (ev?.kind === "update") {
      expect(ev.assistantDelta).toBe("Hi");
      expect(ev.thoughtLines.length).toBeGreaterThan(0);
    }
  });
});
