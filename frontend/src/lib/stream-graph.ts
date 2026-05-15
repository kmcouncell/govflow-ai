import { getPublicEnv } from "@/lib/env";
import { formatObservabilityForThoughtPanel, parseSseDataLine } from "@/lib/graph-sse";
import { joinApiUrl } from "@/lib/url";

export type GraphInvokeMessage = {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  name?: string;
  tool_call_id?: string;
};

export type StreamGraphOptions = {
  messages: GraphInvokeMessage[];
  threadId?: string;
  signal: AbortSignal;
  onAssistantDelta: (delta: string) => void;
  onDone?: (raw: Record<string, unknown>) => void;
  /** Incremental routing / agent signals extracted from each SSE update. */
  onThoughtLines?: (lines: string[]) => void;
};

function parseSseBlocks(buffer: string): { events: string[]; rest: string } {
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";
  return { events: parts, rest };
}

/** Consume graph SSE until completion or abort. */
export async function streamGraphResponse(options: StreamGraphOptions): Promise<void> {
  const env = getPublicEnv();
  const url = joinApiUrl(env.apiBaseUrl, env.graphStreamPath);
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      messages: options.messages,
      thread_id: options.threadId ?? null,
    }),
    signal: options.signal,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Stream request failed (${res.status})`);
  }
  const reader = res.body?.getReader();
  if (!reader) {
    throw new Error("Response body is not readable");
  }
  const decoder = new TextDecoder();
  let carry = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    carry += decoder.decode(value, { stream: true });
    const { events, rest } = parseSseBlocks(carry);
    carry = rest;
    for (const block of events) {
      for (const line of block.split("\n")) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;
        const payload = trimmed.slice(5).trim();
        if (payload === "[DONE]") continue;
        const ev = parseSseDataLine(payload);
        if (!ev) continue;
        if (ev.kind === "update") {
          if (ev.assistantDelta) options.onAssistantDelta(ev.assistantDelta);
          if (ev.thoughtLines.length) options.onThoughtLines?.(ev.thoughtLines);
        }
        if (ev.kind === "done") {
          const raw = ev.raw;
          const obs = raw.observability;
          if (options.onThoughtLines && obs && typeof obs === "object") {
            const tail = formatObservabilityForThoughtPanel(obs as Record<string, unknown>);
            if (tail.length) options.onThoughtLines(tail);
          }
          options.onDone?.(raw);
        }
      }
    }
  }
  if (carry.trim()) {
    for (const block of carry.split("\n\n")) {
      for (const line of block.split("\n")) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;
        const payload = trimmed.slice(5).trim();
        const ev = parseSseDataLine(payload);
        if (!ev) continue;
        if (ev.kind === "update") {
          if (ev.assistantDelta) options.onAssistantDelta(ev.assistantDelta);
          if (ev.thoughtLines.length) options.onThoughtLines?.(ev.thoughtLines);
        }
        if (ev.kind === "done") {
          const raw = ev.raw;
          const obs = raw.observability;
          if (options.onThoughtLines && obs && typeof obs === "object") {
            const tail = formatObservabilityForThoughtPanel(obs as Record<string, unknown>);
            if (tail.length) options.onThoughtLines(tail);
          }
          options.onDone?.(raw);
        }
      }
    }
  }
}

/** Deterministic local stream for demos and tests when the API is unavailable. */
export async function streamMockAssistantResponse(
  userText: string,
  signal: AbortSignal,
  onChunk: (t: string) => void,
): Promise<void> {
  const base =
    "This is an offline preview stream. Connect the GovFlow API to receive live graph updates.\n\nYou asked: ";
  const tail = `\n\n(Thread: ${userText.length} characters.)`;
  const text = `${base}${userText}${tail}`;
  const chunkSize = 8;
  for (let i = 0; i < text.length; i += chunkSize) {
    if (signal.aborted) return;
    onChunk(text.slice(i, i + chunkSize));
    await new Promise<void>((r) => {
      setTimeout(r, 20);
    });
  }
}
