import { describe, expect, it } from "vitest";

import { extractAssistantTextFromSsePayload, parseSseDataLine } from "@/lib/graph-sse";

describe("graph-sse", () => {
  it("extracts assistant text from LangChain-style AI message objects", () => {
    const text = extractAssistantTextFromSsePayload({
      updates: { step: { messages: [{ type: "ai", content: "Hello from graph" }] } },
    });
    expect(text).toBe("Hello from graph");
  });

  it("parses done events", () => {
    const ev = parseSseDataLine(JSON.stringify({ done: true }));
    expect(ev?.kind).toBe("done");
  });
});
