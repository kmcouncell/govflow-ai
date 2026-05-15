import * as React from "react";

import { Badge } from "@/components/ui/badge";
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

  const send = () => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    setError(null);
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
    <div className={cn("mx-auto flex max-w-4xl flex-col gap-4", className)}>
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Streaming assistant</h1>
        <p className="text-sm text-muted-foreground">
          Messages stream from <span className="font-mono">{env.graphStreamPath}</span> when live API is enabled.
          Automatic fallback runs if the backend is unreachable.
        </p>
      </div>

      <Card className="border-border/80 bg-card/60">
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
                <p className="text-sm text-muted-foreground">
                  Ask a policy or workflow question. Assistant output streams token-by-token as SSE chunks arrive.
                </p>
              ) : null}
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={cn(
                    "flex flex-col gap-1 rounded-lg border px-3 py-2 text-sm shadow-sm",
                    m.role === "user"
                      ? "ml-8 border-primary/25 bg-primary/5"
                      : "mr-8 border-muted bg-muted/40",
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {m.role}
                    </span>
                    {m.role === "assistant" && m.streaming ? (
                      <Badge variant="secondary" className="text-[10px]">
                        Streaming
                      </Badge>
                    ) : null}
                  </div>
                  <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
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
              <Button type="button" onClick={send} disabled={!input.trim()}>
                Send
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
