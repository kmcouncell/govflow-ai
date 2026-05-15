import { afterEach, describe, expect, it, vi } from "vitest";

import { getPublicEnv } from "@/lib/env";

describe("getPublicEnv", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("defaults optional feature flags to true", () => {
    vi.stubEnv("VITE_GOVFLOW_API_BASE_URL", "http://localhost:8000");
    vi.stubEnv("VITE_GOVFLOW_APP_NAME", "GovFlow AI");
    vi.stubEnv("VITE_GOVFLOW_ENV", "test");
    vi.stubEnv("VITE_GOVFLOW_GRAPH_STREAM_PATH", "/v1/graph/stream");

    const env = getPublicEnv();
    expect(env.featureAssistant).toBe(true);
    expect(env.featureWorkflow).toBe(true);
  });

  it("parses falsey feature flags", () => {
    vi.stubEnv("VITE_GOVFLOW_API_BASE_URL", "http://localhost:8000");
    vi.stubEnv("VITE_GOVFLOW_APP_NAME", "GovFlow AI");
    vi.stubEnv("VITE_GOVFLOW_ENV", "test");
    vi.stubEnv("VITE_GOVFLOW_GRAPH_STREAM_PATH", "/v1/graph/stream");
    vi.stubEnv("VITE_GOVFLOW_FEATURE_ASSISTANT", "false");
    vi.stubEnv("VITE_GOVFLOW_FEATURE_WORKFLOW", "0");

    const env = getPublicEnv();
    expect(env.featureAssistant).toBe(false);
    expect(env.featureWorkflow).toBe(false);
  });
});
