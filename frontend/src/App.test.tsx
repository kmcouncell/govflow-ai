import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import App from "@/App";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";

function renderApp(initialPath: string) {
  return render(
    <ThemeProvider attribute="class" defaultTheme="light" forcedTheme="light" enableSystem={false}>
      <TooltipProvider>
        <MemoryRouter initialEntries={[initialPath]}>
          <App />
        </MemoryRouter>
      </TooltipProvider>
    </ThemeProvider>,
  );
}

describe("App routing", () => {
  it("renders dashboard on /", () => {
    renderApp("/");
    expect(screen.getByRole("heading", { name: /intelligent dashboard/i })).toBeInTheDocument();
  });

  it("renders assistant on /assistant", () => {
    renderApp("/assistant");
    expect(screen.getByRole("heading", { name: /streaming assistant/i })).toBeInTheDocument();
  });

  it("redirects unknown paths to dashboard", async () => {
    render(
      <ThemeProvider attribute="class" defaultTheme="light" forcedTheme="light" enableSystem={false}>
        <TooltipProvider>
          <MemoryRouter initialEntries={["/unknown-segment"]}>
            <App />
          </MemoryRouter>
        </TooltipProvider>
      </ThemeProvider>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("dashboard-title")).toBeInTheDocument();
    });
    expect(screen.getAllByTestId("dashboard-title")).toHaveLength(1);
  });
});
