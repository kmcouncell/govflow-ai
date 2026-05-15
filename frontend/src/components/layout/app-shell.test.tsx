import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { renderAppWithProviders } from "@/test/render-app";

describe("AppShell feature flags", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("hides assistant + workflow navigation when disabled", () => {
    vi.stubEnv("VITE_GOVFLOW_API_BASE_URL", "http://localhost:8000");
    vi.stubEnv("VITE_GOVFLOW_APP_NAME", "GovFlow AI");
    vi.stubEnv("VITE_GOVFLOW_ENV", "test");
    vi.stubEnv("VITE_GOVFLOW_GRAPH_STREAM_PATH", "/v1/graph/stream");
    vi.stubEnv("VITE_GOVFLOW_FEATURE_ASSISTANT", "false");
    vi.stubEnv("VITE_GOVFLOW_FEATURE_WORKFLOW", "false");

    renderAppWithProviders("/");

    expect(screen.getByRole("link", { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /^assistant$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /^workflow$/i })).not.toBeInTheDocument();
  });
});
