import * as React from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { getPublicEnv } from "@/lib/env";
import type { GraphInvokeMessage } from "@/lib/stream-graph";
import { streamGraphResponse, streamMockAssistantResponse } from "@/lib/stream-graph";
import { cn } from "@/lib/utils";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
};

function toInvokeMessages(rows: ChatMessage[]): GraphInvokeMessage[] {
  return rows.map((m) => ({
    role: m.role,
    content: m.content,
  }));
}

export type StreamingChatProps = {
  className?: string;
};

export function StreamingChat({ className }: StreamingChatProps) {
  const env = getPublicEnv();
  const [input, setInput] = React.useState("");
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [thoughtLines, setThoughtLines] = React.useState<string[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [useLiveApi, setUseLiveApi] = React.useState(true);
  const abortRef = React.useRef<AbortController | null>(null);

  const bottomRef = React.useRef<HTMLDivElement | null>(null);
  React.useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages]);

  const stop = React.useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  React.useEffect(() => () => stop(), [stop]);

  const isStreaming = messages.some((m) => m.role === "assistant" && m.streaming);

  const send = () => {
    const text = input.trim();
    if (!text || isStreaming) return;
    setInput("");
    setError(null);
    setThoughtLines([]);
    stop();

    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };
    const asstId = crypto.randomUUID();
    const controller = new AbortController();
    abortRef.current = controller;

    const bumpAssistant = (delta: string) => {
      if (!delta) return;
      setMessages((prev) =>
        prev.map((m) => (m.id === asstId ? { ...m, content: m.content + delta } : m)),
      );
    };

    const appendThoughts = (lines: string[]) => {
      if (!lines.length) return;
      setThoughtLines((prev) => [...prev, ...lines]);
    };

    const finalize = () => {
      setMessages((prev) => prev.map((m) => (m.id === asstId ? { ...m, streaming: false } : m)));
      abortRef.current = null;
    };

    setMessages((prev) => {
      const invokeRows: ChatMessage[] = [...prev, userMsg];
      void (async () => {
        try {
          if (useLiveApi) {
            await streamGraphResponse({
              messages: toInvokeMessages(invokeRows),
              threadId: undefined,
              signal: controller.signal,
              onAssistantDelta: bumpAssistant,
              onThoughtLines: appendThoughts,
            });
          } else {
            await streamMockAssistantResponse(text, controller.signal, bumpAssistant);
          }
        } catch (e) {
          if ((e as Error).name === "AbortError") {
            return;
          }
          if (useLiveApi) {
            setError((e as Error).message || "Stream failed; showing offline preview.");
            try {
              await streamMockAssistantResponse(text, controller.signal, bumpAssistant);
            } catch {
              /* ignore */
            }
          } else {
            setError((e as Error).message || "Stream failed.");
          }
        } finally {
          finalize();
        }
      })();

      return [...prev, userMsg, { id: asstId, role: "assistant", content: "", streaming: true }];
    });
  };

  return (
    <div className={cn("mx-auto flex max-w-4xl flex-col gap-6 pb-10", className)}>
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Policy assistant</h1>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Streams from <span className="font-mono text-foreground/90">{env.graphStreamPath}</span> when the live API is
          enabled. If the backend is unreachable, the console falls back to an offline preview stream.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="border-border/70 bg-card/70 shadow-sm ring-1 ring-border/40 lg:col-span-2">
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle>Session</CardTitle>
              <CardDescription>User messages are validated by backend guardrails when the API is online.</CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="button"
                size="sm"
                variant={useLiveApi ? "default" : "outline"}
                onClick={() => setUseLiveApi(true)}
              >
                Live API
              </Button>
              <Button
                type="button"
                size="sm"
                variant={!useLiveApi ? "default" : "outline"}
                onClick={() => setUseLiveApi(false)}
              >
                Demo only
              </Button>
              <Button type="button" size="sm" variant="outline" onClick={stop}>
                Stop
              </Button>
            </div>
          </CardHeader>
          <Separator />
          <CardContent className="p-0">
            <ScrollArea className="h-[min(60vh,520px)] p-4">
              <div className="space-y-4 pr-3">
                {messages.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-border/80 bg-muted/20 p-6 text-center">
                    <p className="text-sm font-medium text-foreground">Start a conversation</p>
                    <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                      Ask about telework documentation, records retention, FOIA steps, or acquisition thresholds from the
                      sample corpus. Messages are validated by backend guardrails when online.
                    </p>
                  </div>
                ) : null}
                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={cn(
                      "flex flex-col gap-1 rounded-lg border px-3 py-2 text-sm shadow-sm",
                      m.role === "user"
                        ? "ml-6 border-primary/30 bg-primary/10 sm:ml-10"
                        : "mr-6 border-border bg-muted/35 sm:mr-10",
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        {m.role}
                      </span>
                      {m.role === "assistant" && m.streaming ? (
                        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-primary">
                          <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
                          Streaming
                        </span>
                      ) : null}
                    </div>
                    <p className="whitespace-pre-wrap leading-relaxed">
                      {m.content}
                      {m.role === "assistant" && m.streaming && !m.content ? (
                        <span className="inline-flex items-center gap-2 text-muted-foreground">
                          <Loader2 className="h-4 w-4 animate-spin shrink-0" aria-hidden />
                          Awaiting first token…
                        </span>
                      ) : null}
                    </p>
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
            </ScrollArea>
            <Separator />
            <div className="space-y-2 p-4">
              {error ? <p className="text-xs text-destructive">{error}</p> : null}
              <Textarea
                placeholder="Type your message… (Shift+Enter for newline)"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                rows={3}
              />
              <div className="flex justify-end">
                <Button type="button" onClick={send} disabled={!input.trim() || isStreaming}>
                  {isStreaming ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                      Sending
                    </>
                  ) : (
                    "Send"
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/70 bg-card/70 shadow-sm ring-1 ring-border/40">
          <CardHeader>
            <CardTitle className="text-base">Agent reasoning</CardTitle>
            <CardDescription className="text-xs">
              Routing signals per SSE update, plus observability totals when the stream completes.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[min(60vh,520px)] px-4 pb-4">
              {thoughtLines.length === 0 ? (
                <p className="text-xs text-muted-foreground">Thought lines appear as the graph advances.</p>
              ) : (
                <ul className="space-y-2 pr-3 text-xs leading-relaxed">
                  {thoughtLines.map((line, i) => (
                    <li key={`${i}-${line.slice(0, 24)}`} className="rounded-md border bg-muted/30 px-2 py-1.5 font-mono">
                      {line}
                    </li>
                  ))}
                </ul>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
