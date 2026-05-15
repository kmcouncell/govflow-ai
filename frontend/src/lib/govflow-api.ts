/**
 * GovFlow backend HTTP helpers. Paths are fixed API contract; base URL from `getPublicEnv()`.
 */

import { getPublicEnv } from "@/lib/env";
import { joinApiUrl } from "@/lib/url";

import type { GraphInvokeMessage } from "@/lib/stream-graph";

export type HealthLiveResponse = { status: string };

export type HealthReadyResponse = {
  status: string;
  environment?: string;
  sample_data_dir_exists?: boolean;
};

export type GraphDemoResult = {
  result: {
    messages: unknown[];
    observability: Record<string, unknown>;
    last_route?: string | null;
    last_active_agent?: string | null;
    guardrails?: Record<string, unknown>;
    request_latency_ms?: number;
  };
};

export type GraphInvokeResponseBody = {
  messages: unknown[];
  observability: Record<string, unknown>;
  active_agent?: string | null;
  guardrails?: Record<string, unknown>;
  request_latency_ms?: number | null;
};

export type RagQueryResponseBody = {
  answer: string;
  citations?: unknown[];
  guardrails?: Record<string, unknown>;
  request_latency_ms?: number;
  [key: string]: unknown;
};

export class GovflowApiError extends Error {
  readonly status: number;
  readonly bodyText: string;

  constructor(message: string, status: number, bodyText: string) {
    super(message);
    this.name = "GovflowApiError";
    this.status = status;
    this.bodyText = bodyText;
  }
}

async function readJsonOrText(res: Response): Promise<{ json: unknown | null; text: string }> {
  const text = await res.text();
  try {
    return { json: JSON.parse(text) as unknown, text };
  } catch {
    return { json: null, text };
  }
}

function apiUrl(path: string): string {
  const { apiBaseUrl } = getPublicEnv();
  return joinApiUrl(apiBaseUrl, path);
}

export async function fetchHealthLive(signal?: AbortSignal): Promise<HealthLiveResponse> {
  const res = await fetch(apiUrl("/health/live"), { signal });
  const { json, text } = await readJsonOrText(res);
  if (!res.ok) {
    throw new GovflowApiError(text || `HTTP ${res.status}`, res.status, text);
  }
  return (json ?? { status: "unknown" }) as HealthLiveResponse;
}

export async function fetchHealthReady(signal?: AbortSignal): Promise<HealthReadyResponse> {
  const res = await fetch(apiUrl("/health/ready"), { signal });
  const { json, text } = await readJsonOrText(res);
  if (!res.ok) {
    throw new GovflowApiError(text || `HTTP ${res.status}`, res.status, text);
  }
  return (json ?? {}) as HealthReadyResponse;
}

export async function postGraphDemo(signal?: AbortSignal): Promise<GraphDemoResult> {
  const res = await fetch(apiUrl("/v1/graph/demo"), { method: "POST", signal });
  const { json, text } = await readJsonOrText(res);
  if (!res.ok) {
    throw new GovflowApiError(text || `HTTP ${res.status}`, res.status, text);
  }
  if (!json || typeof json !== "object") {
    throw new GovflowApiError("Invalid graph demo response", res.status, text);
  }
  return json as GraphDemoResult;
}

export async function postGraphInvoke(
  body: { messages: GraphInvokeMessage[]; thread_id?: string | null },
  signal?: AbortSignal,
): Promise<GraphInvokeResponseBody> {
  const res = await fetch(apiUrl("/v1/graph/invoke"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: body.messages,
      thread_id: body.thread_id ?? null,
    }),
    signal,
  });
  const { json, text } = await readJsonOrText(res);
  if (!res.ok) {
    throw new GovflowApiError(text || `HTTP ${res.status}`, res.status, text);
  }
  if (!json || typeof json !== "object") {
    throw new GovflowApiError("Invalid graph invoke response", res.status, text);
  }
  return json as GraphInvokeResponseBody;
}

export async function postRagQuery(
  body: { question: string; top_k?: number; metadata_filter?: Record<string, unknown> | null },
  signal?: AbortSignal,
): Promise<RagQueryResponseBody> {
  const res = await fetch(apiUrl("/v1/rag/query"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: body.question,
      top_k: body.top_k,
      metadata_filter: body.metadata_filter ?? null,
    }),
    signal,
  });
  const { json, text } = await readJsonOrText(res);
  if (!res.ok) {
    throw new GovflowApiError(text || `HTTP ${res.status}`, res.status, text);
  }
  if (!json || typeof json !== "object") {
    throw new GovflowApiError("Invalid RAG response", res.status, text);
  }
  return json as RagQueryResponseBody;
}

export async function postRagIngest(
  body: { reset?: boolean },
  signal?: AbortSignal,
): Promise<{ documents_loaded: number; chunks_indexed: number }> {
  const res = await fetch(apiUrl("/v1/rag/ingest"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reset: body.reset ?? false }),
    signal,
  });
  const { json, text } = await readJsonOrText(res);
  if (!res.ok) {
    throw new GovflowApiError(text || `HTTP ${res.status}`, res.status, text);
  }
  if (!json || typeof json !== "object") {
    throw new GovflowApiError("Invalid ingest response", res.status, text);
  }
  return json as { documents_loaded: number; chunks_indexed: number };
}
