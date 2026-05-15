import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle, Brain, Cpu, LineChart, Loader2, RefreshCw, ShieldCheck } from "lucide-react";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { getPublicEnv } from "@/lib/env";
import {
  GovflowApiError,
  fetchHealthLive,
  fetchHealthReady,
  postGraphDemo,
  postRagQuery,
} from "@/lib/govflow-api";
import { queryKeys } from "@/lib/query-keys";

function buildInsightsFromObservability(obs: Record<string, unknown> | undefined): {
  title: string;
  body: string;
  icon: typeof Brain;
}[] {
  if (!obs || typeof obs !== "object") {
    return [
      {
        title: "Telemetry pending",
        body: "Load an agent snapshot to synthesize routing and token signals for this console.",
        icon: Brain,
      },
      {
        title: "Responsible AI posture",
        body: "Guardrails are enforced server-side on invoke, stream, and RAG paths.",
        icon: ShieldCheck,
      },
      {
        title: "Capacity",
        body: "Connect live traffic metrics when observability export is wired; UI degrades cleanly if the API is offline.",
        icon: Cpu,
      },
    ];
  }
  const events = Array.isArray(obs.events) ? obs.events : [];
  const llm = events.filter((e) => e && typeof e === "object" && (e as { kind?: string }).kind === "llm").length;
  const tools = events.filter((e) => e && typeof e === "object" && (e as { kind?: string }).kind === "tool").length;
  const totals = obs.totals && typeof obs.totals === "object" ? (obs.totals as Record<string, unknown>) : {};
  const latency = typeof totals.latency_ms === "number" ? totals.latency_ms.toFixed(0) : "—";

  return [
    {
      title: "Latest agent snapshot",
      body: `Last demo run recorded ${llm} LLM hop(s) and ${tools} tool interaction(s); tracked latency ≈ ${latency} ms.`,
      icon: Brain,
    },
    {
      title: "Responsible AI posture",
      body: "PII and topic guardrails run on the backend. Review audit logs for blocked requests in production.",
      icon: ShieldCheck,
    },
    {
      title: "Grounding",
      body: "Use RAG quick check below against your indexed corpus. Citations appear when retrieval succeeds.",
      icon: Cpu,
    },
  ];
}

export function DashboardPage() {
  const env = getPublicEnv();

  const live = useQuery({
    queryKey: queryKeys.healthLive,
    queryFn: ({ signal }) => fetchHealthLive(signal),
    staleTime: 15_000,
  });
  const ready = useQuery({
    queryKey: queryKeys.healthReady,
    queryFn: ({ signal }) => fetchHealthReady(signal),
    staleTime: 15_000,
  });
  const demo = useQuery({
    queryKey: queryKeys.graphDemo,
    queryFn: ({ signal }) => postGraphDemo(signal),
    staleTime: 5 * 60_000,
    retry: 1,
  });

  const ragMutation = useMutation({
    mutationFn: (question: string) => postRagQuery({ question, top_k: 5 }),
  });

  const [ragQuestion, setRagQuestion] = React.useState(
    "What telework documentation must supervisors retain per the sample OMB memorandum?",
  );

  const apiDown = live.isError;
  const obs = demo.data?.result?.observability as Record<string, unknown> | undefined;
  const totals = obs?.totals && typeof obs.totals === "object" ? (obs.totals as Record<string, unknown>) : {};
  const latencyMs = typeof totals.latency_ms === "number" ? `${totals.latency_ms.toFixed(0)} ms` : "—";
  const insights = buildInsightsFromObservability(obs);

  const metrics = [
    {
      label: "API liveness",
      value: live.data?.status === "ok" ? "Healthy" : live.isLoading ? "…" : "Unknown",
      delta: live.isError ? "unreachable" : "polling",
      tone: live.data?.status === "ok" ? ("success" as const) : ("secondary" as const),
    },
    {
      label: "Readiness",
      value: ready.data?.status === "ok" ? "Ready" : ready.isLoading ? "…" : "Check",
      delta: ready.data?.sample_data_dir_exists === false ? "sample dir missing" : "ok",
      tone: ready.data?.status === "ok" ? ("success" as const) : ("secondary" as const),
    },
    {
      label: "Agent snapshot latency",
      value: demo.isLoading ? "…" : demo.isError ? "—" : latencyMs,
      delta: demo.isError ? "demo failed" : "last graph/demo",
      tone: demo.isError ? ("secondary" as const) : ("success" as const),
    },
    {
      label: "RAG quick check",
      value: ragMutation.isPending ? "Running…" : ragMutation.isSuccess ? "Answered" : "Idle",
      delta: ragMutation.isError ? "error" : "mutation",
      tone: ragMutation.isError ? ("secondary" as const) : ("secondary" as const),
    },
  ];

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-10 pb-10">
      {apiDown ? (
        <Card className="border-amber-500/40 bg-amber-500/5">
          <CardHeader className="flex flex-row items-start gap-2 pb-2">
            <AlertCircle className="h-5 w-5 shrink-0 text-amber-600" />
            <div>
              <CardTitle className="text-base">API unreachable</CardTitle>
              <CardDescription>
                Dashboard metrics fall back to placeholders. Confirm <span className="font-mono">{env.apiBaseUrl}</span>{" "}
                is running and CORS allows this origin.
              </CardDescription>
            </div>
          </CardHeader>
        </Card>
      ) : null}

      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <h1
            data-testid="dashboard-title"
            className="text-2xl font-semibold tracking-tight text-foreground md:text-3xl"
          >
            Operations dashboard
          </h1>
          <Badge variant="outline">{env.environment}</Badge>
          {live.isFetching || ready.isFetching ? (
            <Badge variant="secondary" className="font-normal">
              Refreshing
            </Badge>
          ) : null}
        </div>
        <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground md:text-base">
          Health and readiness for the GovFlow API, an optional LangGraph snapshot, and a quick retrieval check against
          the indexed Markdown corpus. Panels stay usable when the API is offline.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => {
              void live.refetch();
              void ready.refetch();
            }}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh health
          </Button>
          <Button type="button" size="sm" variant="outline" onClick={() => void demo.refetch()} disabled={demo.isFetching}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh agent snapshot
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((m) => (
          <Card key={m.label} className="border-border/70 bg-card/70 shadow-sm ring-1 ring-border/40">
            <CardHeader className="pb-2">
              <CardDescription>{m.label}</CardDescription>
              {live.isLoading && m.label === "API liveness" ? (
                <Skeleton className="h-8 w-24" />
              ) : (
                <CardTitle className="text-2xl tabular-nums">{m.value}</CardTitle>
              )}
            </CardHeader>
            <CardContent>
              <Badge variant={m.tone === "success" ? "success" : "secondary"} className="font-normal">
                {m.delta}
              </Badge>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="border-border/70 bg-card/70 shadow-sm ring-1 ring-border/40 lg:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-2">
              <LineChart className="h-5 w-5 text-primary" />
              <CardTitle>Throughput &amp; quality</CardTitle>
            </div>
            <CardDescription>Snapshot from <span className="font-mono">POST /v1/graph/demo</span> (supervisor graph).</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {demo.isLoading ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <Skeleton className="h-28 w-full" />
                <Skeleton className="h-28 w-full" />
              </div>
            ) : demo.isError ? (
              <p className="text-sm text-destructive">
                {demo.error instanceof GovflowApiError ? demo.error.message : String(demo.error)}
              </p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border bg-muted/30 p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Last route</p>
                  <p className="mt-2 text-xl font-semibold tabular-nums">
                    {String(demo.data?.result?.last_route ?? "—")}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">From demo state</p>
                </div>
                <div className="rounded-lg border bg-muted/30 p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Tracked calls</p>
                  <p className="mt-2 text-xl font-semibold tabular-nums">
                    {Array.isArray(obs?.events) ? obs.events.length : 0}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">LLM + tool events</p>
                </div>
              </div>
            )}
            <Separator />
            <div className="space-y-2">
              <p className="text-sm font-medium">RAG quick check</p>
              <div className="flex flex-col gap-2 sm:flex-row">
                <Input value={ragQuestion} onChange={(e) => setRagQuestion(e.target.value)} className="flex-1" />
                <Button
                  type="button"
                  disabled={!ragQuestion.trim() || ragMutation.isPending}
                  onClick={() => ragMutation.mutate(ragQuestion.trim())}
                >
                  {ragMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                      Running
                    </>
                  ) : (
                    "Ask"
                  )}
                </Button>
              </div>
              {ragMutation.isError ? (
                <p className="text-xs text-destructive">
                  {ragMutation.error instanceof GovflowApiError ? ragMutation.error.message : String(ragMutation.error)}
                </p>
              ) : null}
              {ragMutation.isSuccess ? (
                <div className="rounded-md border bg-background/80 p-3 text-sm leading-relaxed">
                  <p className="whitespace-pre-wrap">{ragMutation.data.answer}</p>
                  {Array.isArray(ragMutation.data.citations) && ragMutation.data.citations.length ? (
                    <p className="mt-2 text-xs text-muted-foreground">
                      {ragMutation.data.citations.length} citation(s) returned.
                    </p>
                  ) : null}
                </div>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/70 bg-card/70 shadow-sm ring-1 ring-border/40">
          <CardHeader>
            <CardTitle>AI insights</CardTitle>
            <CardDescription>Derived from the latest successful agent snapshot when available.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {insights.map(({ title, body, icon: Icon }) => (
              <div key={title} className="flex gap-3 rounded-lg border bg-background/60 p-3">
                <div className="mt-0.5 text-primary">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium leading-none">{title}</p>
                  <p className="text-xs text-muted-foreground leading-relaxed">{body}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
