/**
 * Parse SSE `data: {...}` payloads from the graph stream endpoint
 * (`POST /v1/graph/stream`) and extract assistant-visible text when present.
 */

export function extractAssistantTextFromSsePayload(parsed: Record<string, unknown>): string {
  if (parsed.done === true) return "";
  const updates = parsed.updates;
  if (updates === undefined || updates === null) return "";
  const parts: string[] = [];
  const walk = (node: unknown): void => {
    if (node === null || node === undefined) return;
    if (Array.isArray(node)) {
      for (const item of node) walk(item);
      return;
    }
    if (typeof node !== "object") return;
    const o = node as Record<string, unknown>;
    if (o.type === "ai" && typeof o.content === "string") {
      parts.push(o.content);
    }
    if (o.role === "assistant" && typeof o.content === "string") {
      parts.push(o.content);
    }
    for (const v of Object.values(o)) walk(v);
  };
  walk(updates);
  return parts.join("");
}

export type GraphStreamEvent =
  | { kind: "update"; assistantDelta: string; raw: Record<string, unknown> }
  | { kind: "done"; raw: Record<string, unknown> }
  | { kind: "unknown"; raw: Record<string, unknown> };

export function parseSseDataLine(jsonText: string): GraphStreamEvent | null {
  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(jsonText) as Record<string, unknown>;
  } catch {
    return null;
  }
  if (parsed.done === true) return { kind: "done", raw: parsed };
  if ("updates" in parsed) {
    const delta = extractAssistantTextFromSsePayload(parsed);
    return { kind: "update", assistantDelta: delta, raw: parsed };
  }
  return { kind: "unknown", raw: parsed };
}
