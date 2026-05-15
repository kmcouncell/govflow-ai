import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { renderAppWithProviders } from "@/test/render-app";

describe("App routing", () => {
  it("renders dashboard on /", () => {
    renderAppWithProviders("/");
    expect(screen.getByRole("heading", { name: /operations dashboard/i })).toBeInTheDocument();
  });

  it("renders assistant on /assistant", () => {
    renderAppWithProviders("/assistant");
    expect(screen.getByRole("heading", { name: /policy assistant/i })).toBeInTheDocument();
  });

  it("renders workflow simulator on /workflow", () => {
    renderAppWithProviders("/workflow");
    expect(screen.getByRole("heading", { name: /workflow simulator/i })).toBeInTheDocument();
  });

  it("redirects unknown paths to dashboard", async () => {
    renderAppWithProviders("/unknown-segment");
    await waitFor(() => {
      expect(screen.getByTestId("dashboard-title")).toBeInTheDocument();
    });
    expect(screen.getAllByTestId("dashboard-title")).toHaveLength(1);
  });
});
