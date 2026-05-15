import { useMutation } from "@tanstack/react-query";
import { GitBranch, Play, Sparkles } from "lucide-react";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { GovflowApiError, postGraphInvoke } from "@/lib/govflow-api";
import { getPublicEnv } from "@/lib/env";
import type { GraphInvokeMessage } from "@/lib/stream-graph";

const PRESETS: { id: string; label: string; description: string; messages: GraphInvokeMessage[] }[] = [
  {
    id: "workflow",
    label: "Permit workflow",
    description: "Routes toward the workflow specialist for procedural guidance.",
    messages: [{ role: "user", content: "Walk me through the standard intake workflow for a new permit application." }],
  },
  {
    id: "research",
    label: "Research mode",
    description: "Keyword “research” steers degraded routing toward the research agent.",
    messages: [{ role: "user", content: "Research the policy references we should cite for remote work eligibility." }],
  },
  {
    id: "document",
    label: "Document analysis",
    description: "Steers toward the document analyzer when LLM is offline (keyword heuristics).",
    messages: [{ role: "user", content: "Analyze this PDF outline for PII before we publish it externally." }],
  },
];

export function WorkflowSimulatorPage() {
  const env = getPublicEnv();
  const [presetId, setPresetId] = React.useState(PRESETS[0].id);
  const preset = PRESETS.find((p) => p.id === presetId) ?? PRESETS[0];

  const invoke = useMutation({
    mutationFn: () => postGraphInvoke({ messages: preset.messages, thread_id: null }),
  });

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <div className="space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">Interactive workflow simulator</h1>
          <Badge variant="outline">{env.environment}</Badge>
        </div>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Each scenario calls <span className="font-mono">POST /v1/graph/invoke</span> with a preset user message. Inspect
          JSON output, guardrails summary, and observability to validate routing before go-live.
        </p>
      </div>

      <Card className="border-border/80 bg-card/60">
        <CardHeader>
          <div className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-primary" />
            <CardTitle>Scenarios</CardTitle>
          </div>
          <CardDescription>Select a preset, then run the graph once (non-streaming invoke).</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {PRESETS.map((p) => (
              <Button
                key={p.id}
                type="button"
                size="sm"
                variant={p.id === presetId ? "default" : "outline"}
                onClick={() => setPresetId(p.id)}
              >
                {p.label}
              </Button>
            ))}
          </div>
          <p className="text-sm text-muted-foreground">{preset.description}</p>
          <div className="flex flex-wrap items-center gap-2">
            <Button type="button" onClick={() => invoke.mutate()} disabled={invoke.isPending}>
              <Play className="mr-2 h-4 w-4" />
              {invoke.isPending ? "Running…" : "Run agents"}
            </Button>
            {invoke.isSuccess ? (
              <Badge variant="secondary" className="font-mono text-xs">
                active_agent: {String(invoke.data.active_agent ?? "null")}
              </Badge>
            ) : null}
          </div>
          {invoke.isError ? (
            <p className="text-sm text-destructive">
              {invoke.error instanceof GovflowApiError ? invoke.error.message : String(invoke.error)}
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card className="border-border/80 bg-card/60">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <CardTitle>Invoke result</CardTitle>
          </div>
          <CardDescription>Raw response body (messages redacted length-safe in production UIs).</CardDescription>
        </CardHeader>
        <Separator />
        <CardContent className="p-0">
          <ScrollArea className="h-[min(55vh,480px)] p-4">
            {invoke.isSuccess ? (
              <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-relaxed">
                {JSON.stringify(invoke.data, null, 2)}
              </pre>
            ) : (
              <p className="text-sm text-muted-foreground">Run a scenario to see structured graph output.</p>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
