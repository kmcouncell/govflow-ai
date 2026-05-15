import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { StreamingChat } from "@/components/chat/streaming-chat";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";

function renderChat() {
  return render(
    <ThemeProvider attribute="class" defaultTheme="light" forcedTheme="light" enableSystem={false}>
      <TooltipProvider>
        <StreamingChat />
      </TooltipProvider>
    </ThemeProvider>,
  );
}

describe("StreamingChat", () => {
  it("streams demo text when demo mode is selected", async () => {
    const user = userEvent.setup();
    renderChat();
    await user.click(screen.getByRole("button", { name: /demo only/i }));
    await user.type(screen.getByPlaceholderText(/type your message/i), "Hello agency");
    await user.click(screen.getByRole("button", { name: /^send$/i }));
    await waitFor(
      () => {
        expect(screen.getByText(/offline preview stream/i)).toBeInTheDocument();
      },
      { timeout: 4000 },
    );
    await waitFor(() => {
      expect(screen.getByText(/Hello agency/)).toBeInTheDocument();
    });
  });
});
