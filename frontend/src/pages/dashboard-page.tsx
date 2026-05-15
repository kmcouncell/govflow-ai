import { Brain, Cpu, LineChart, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { getPublicEnv } from "@/lib/env";

const metrics = [
  { label: "Requests (24h)", value: "12.4k", delta: "+4.2%", tone: "success" as const },
  { label: "P95 latency", value: "420 ms", delta: "-18 ms", tone: "success" as const },
  { label: "Guardrail blocks", value: "37", delta: "stable", tone: "secondary" as const },
  { label: "RAG citations / answer", value: "3.1", delta: "+0.2", tone: "secondary" as const },
];

const insights = [
  {
    title: "Routing stability",
    body: "Supervisor hand-offs to the document analyzer rose after the policy corpus update. Consider tuning retrieval thresholds for HR templates.",
    icon: Brain,
  },
  {
    title: "Responsible AI posture",
    body: "PII redaction and topic filters are active. No elevated false-positive rate detected in the last audit window.",
    icon: ShieldCheck,
  },
  {
    title: "Capacity",
    body: "Embedding queue depth is nominal. Scale-out is not indicated unless concurrent sessions exceed the forecast band.",
    icon: Cpu,
  },
];

export function DashboardPage() {
  const env = getPublicEnv();
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8">
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <h1 data-testid="dashboard-title" className="text-2xl font-semibold tracking-tight md:text-3xl">Intelligent dashboard</h1>
          <Badge variant="outline">{env.environment}</Badge>
        </div>
        <p className="max-w-3xl text-sm text-muted-foreground md:text-base">
          Executive view of GovFlow throughput, latency, and AI-assisted signals. Metrics shown are representative
          placeholders until wired to live telemetry.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((m) => (
          <Card key={m.label} className="border-border/80 bg-card/60 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription>{m.label}</CardDescription>
              <CardTitle className="text-2xl tabular-nums">{m.value}</CardTitle>
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
        <Card className="border-border/80 bg-card/60 lg:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-2">
              <LineChart className="h-5 w-5 text-primary" />
              <CardTitle>Throughput & quality</CardTitle>
            </div>
            <CardDescription>Blended view of agent completions, RAG grounding, and policy checks.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border bg-muted/30 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Agent sessions</p>
                <p className="mt-2 text-3xl font-semibold tabular-nums">842</p>
                <p className="mt-1 text-xs text-muted-foreground">Rolling 7 days</p>
              </div>
              <div className="rounded-lg border bg-muted/30 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Grounded answers</p>
                <p className="mt-2 text-3xl font-semibold tabular-nums">96.2%</p>
                <p className="mt-1 text-xs text-muted-foreground">With at least one citation</p>
              </div>
            </div>
            <Separator />
            <p className="text-sm text-muted-foreground">
              Connect observability exports to render live charts. The layout reserves space for sparklines and anomaly
              markers aligned to audit events.
            </p>
          </CardContent>
        </Card>

        <Card className="border-border/80 bg-card/60">
          <CardHeader>
            <CardTitle>AI insights</CardTitle>
            <CardDescription>Curated signals for operators and compliance reviewers.</CardDescription>
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
