import type { ReactElement, ReactNode } from "react";
import { render, type RenderOptions } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "@/App";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { GovflowQueryProvider } from "@/providers/query-provider";

export function renderAppWithProviders(
  initialPath: string,
  options?: Omit<RenderOptions, "wrapper">,
) {
  const Wrapper = ({ children }: { children: ReactNode }): ReactElement => (
    <GovflowQueryProvider>
      <ThemeProvider attribute="class" defaultTheme="light" forcedTheme="light" enableSystem={false}>
        <TooltipProvider>
          <MemoryRouter initialEntries={[initialPath]}>{children}</MemoryRouter>
        </TooltipProvider>
      </ThemeProvider>
    </GovflowQueryProvider>
  );
  return render(<App />, { wrapper: Wrapper, ...options });
}
