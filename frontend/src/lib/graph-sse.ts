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

function tryParseSupervisorRationale(content: string): string | null {
  const t = content.trim();
  if (!t.startsWith("{")) return null;
  try {
    const o = JSON.parse(t) as Record<string, unknown>;
    const r = o.rationale;
    if (typeof r === "string" && r.trim()) return r.trim();
    const n = o.next;
    if (typeof n === "string") return `Structured decision: next → ${n}`;
  } catch {
    return null;
  }
  return null;
}

/** Human-readable lines for the “thought process” panel (routing, agents, rationale snippets). */
export function extractThoughtLinesFromSsePayload(parsed: Record<string, unknown>): string[] {
  if (parsed.done === true) return [];
  const updates = parsed.updates;
  if (updates === undefined || updates === null || typeof updates !== "object") return [];
  const lines: string[] = [];
  const u = updates as Record<string, unknown>;

  for (const [nodeName, nodePayload] of Object.entries(u)) {
    if (!nodePayload || typeof nodePayload !== "object") continue;
    const p = nodePayload as Record<string, unknown>;

    if (typeof p.last_route === "string" && p.last_route) {
      lines.push(`[${nodeName}] Route: ${p.last_route}`);
    }
    if (typeof p.last_active_agent === "string" && p.last_active_agent) {
      lines.push(`[${nodeName}] Active agent: ${p.last_active_agent}`);
    }

    const msgs = p.messages;
    if (Array.isArray(msgs)) {
      for (const m of msgs) {
        if (!m || typeof m !== "object") continue;
        const msg = m as Record<string, unknown>;
        if (msg.type === "ai" && typeof msg.content === "string") {
          const rationale = tryParseSupervisorRationale(msg.content);
          if (rationale) {
            lines.push(`[${nodeName}] Supervisor rationale: ${rationale}`);
          }
        }
      }
    }
  }
  return lines;
}

export function formatObservabilityForThoughtPanel(obs: Record<string, unknown>): string[] {
  const lines: string[] = [];
  const totals = obs.totals;
  if (totals && typeof totals === "object") {
    const t = totals as Record<string, unknown>;
    const lat = t.latency_ms;
    const cost = t.estimated_cost_usd;
    const it = t.input_tokens;
    const ot = t.output_tokens;
    if (typeof lat === "number") lines.push(`Run latency (tracked calls): ${lat.toFixed(0)} ms`);
    if (typeof it === "number" || typeof ot === "number") {
      lines.push(`Tokens — in: ${it ?? "—"}, out: ${ot ?? "—"}`);
    }
    if (typeof cost === "number") lines.push(`Estimated cost (config pricing): $${cost.toFixed(6)}`);
  }
  const events = obs.events;
  if (!Array.isArray(events)) return lines;
  for (const e of events) {
    if (!e || typeof e !== "object") continue;
    const ev = e as Record<string, unknown>;
    if (ev.kind === "llm") {
      const agent = typeof ev.agent === "string" ? ev.agent : "?";
      const ms = typeof ev.latency_ms === "number" ? `${ev.latency_ms.toFixed(0)} ms` : "?";
      lines.push(`LLM · ${agent} · ${ms}`);
    } else if (ev.kind === "tool") {
      const agent = typeof ev.agent === "string" ? ev.agent : "?";
      const tool = typeof ev.tool_name === "string" ? ev.tool_name : "?";
      const ok = ev.ok === true ? "ok" : "failed";
      lines.push(`Tool · ${agent} · ${tool} · ${ok}`);
    }
  }
  return lines;
}

export type GraphStreamEvent =
  | { kind: "update"; assistantDelta: string; thoughtLines: string[]; raw: Record<string, unknown> }
  | { kind: "done"; raw: Record<string, unknown> }
  | { kind: "error"; message: string; raw: Record<string, unknown> }
  | { kind: "unknown"; raw: Record<string, unknown> };

export function parseSseDataLine(jsonText: string): GraphStreamEvent | null {
  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(jsonText) as Record<string, unknown>;
  } catch {
    return null;
  }
  if (parsed.error === true) {
    const detail = typeof parsed.detail === "string" ? parsed.detail : "stream_error";
    return { kind: "error", message: detail, raw: parsed };
  }
  if (parsed.done === true) return { kind: "done", raw: parsed };
  if ("updates" in parsed) {
    const delta = extractAssistantTextFromSsePayload(parsed);
    const thoughtLines = extractThoughtLinesFromSsePayload(parsed);
    return { kind: "update", assistantDelta: delta, thoughtLines, raw: parsed };
  }
  return { kind: "unknown", raw: parsed };
}
