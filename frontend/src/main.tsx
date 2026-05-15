import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { ErrorBoundary } from "@/components/error-boundary";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { GovflowQueryProvider } from "@/providers/query-provider";
import "./index.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <GovflowQueryProvider>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
        <TooltipProvider delayDuration={200}>
          <BrowserRouter>
            <ErrorBoundary title="Application error">
              <App />
            </ErrorBoundary>
          </BrowserRouter>
        </TooltipProvider>
      </ThemeProvider>
    </GovflowQueryProvider>
  </StrictMode>,
);
