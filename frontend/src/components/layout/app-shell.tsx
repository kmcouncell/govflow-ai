import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import type { LucideIcon } from "lucide-react";
import { Activity, GitBranch, LayoutDashboard, Loader2, Menu, MessageSquare, Shield } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { ErrorBoundary } from "@/components/error-boundary";
import { ModeToggle } from "@/components/mode-toggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { getPublicEnv } from "@/lib/env";
import { fetchHealthLive } from "@/lib/govflow-api";
import { queryKeys } from "@/lib/query-keys";
import { cn } from "@/lib/utils";

const nav: Array<{
  to: string;
  label: string;
  icon: LucideIcon;
  end: boolean;
  feature?: "assistant" | "workflow";
}> = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/assistant", label: "Assistant", icon: MessageSquare, end: false, feature: "assistant" },
  { to: "/workflow", label: "Workflow", icon: GitBranch, end: false, feature: "workflow" },
];

function NavItems({
  env,
  onNavigate,
}: {
  env: ReturnType<typeof getPublicEnv>;
  onNavigate?: () => void;
}) {
  const items = nav.filter((item) => {
    if (item.feature === "assistant") {
      return env.featureAssistant;
    }
    if (item.feature === "workflow") {
      return env.featureWorkflow;
    }
    return true;
  });

  return (
    <nav className="flex flex-col gap-1 px-2">
      {items.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-2 rounded-md px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              isActive
                ? "bg-primary/12 text-primary shadow-sm dark:bg-primary/20"
                : "text-muted-foreground hover:bg-muted/80 hover:text-foreground",
            )
          }
        >
          <Icon className="h-4 w-4 shrink-0" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

export function AppShell() {
  const env = getPublicEnv();
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const location = useLocation();
  const live = useQuery({
    queryKey: queryKeys.healthLive,
    queryFn: ({ signal }) => fetchHealthLive(signal),
    staleTime: 20_000,
    retry: 1,
  });

  return (
    <div className="flex min-h-dvh w-full bg-gradient-to-b from-background to-muted/30">
      <aside className="hidden w-64 shrink-0 border-r border-border/80 bg-card/50 shadow-sm backdrop-blur-sm md:flex md:flex-col">
        <div className="flex h-16 items-center gap-3 border-b border-border/80 px-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-xs font-bold tracking-tight text-primary-foreground shadow-sm">
            GF
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold leading-tight tracking-tight">{env.appName}</p>
            <p className="text-xs text-muted-foreground">Federal operations console</p>
          </div>
        </div>
        <div className="flex-1 py-5">
          <NavItems env={env} />
        </div>
        <div className="border-t border-border/80 p-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Shield className="h-3.5 w-3.5 shrink-0 text-primary/80" />
            <span>Guardrails and audit-ready defaults</span>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 flex h-16 items-center gap-3 border-b border-border/80 bg-background/90 px-4 shadow-sm backdrop-blur-md md:px-6">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="sm" className="md:hidden" aria-label="Open navigation menu">
                <Menu className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent className="w-64 border-r p-0">
              <SheetHeader className="border-b p-4 text-left">
                <SheetTitle className="text-base">{env.appName}</SheetTitle>
              </SheetHeader>
              <div className="py-4">
                <NavItems env={env} onNavigate={() => setMobileOpen(false)} />
              </div>
            </SheetContent>
          </Sheet>
          <div className="flex min-w-0 flex-1 items-center gap-2">
            <Activity className="hidden h-4 w-4 text-muted-foreground sm:block" />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold tracking-tight">Mission overview</p>
              <p className="truncate text-xs text-muted-foreground">
                Environment <span className="font-mono text-foreground/80">{env.environment}</span>
              </p>
            </div>
          </div>
          <div className="hidden items-center gap-2 sm:flex">
            <Badge
              variant="outline"
              className={cn(
                "min-w-[5.5rem] justify-center font-mono text-xs tabular-nums",
                live.isSuccess && "border-emerald-500/45 text-emerald-800 dark:text-emerald-400",
                live.isError && "border-destructive/40 text-destructive",
              )}
            >
              {live.isLoading ? (
                <span className="inline-flex items-center gap-1.5">
                  <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
                  Checking
                </span>
              ) : live.isError ? (
                "API offline"
              ) : (
                "API live"
              )}
            </Badge>
            <Badge variant="outline" className="font-mono text-xs">
              {env.apiBaseUrl.replace(/^https?:\/\//, "")}
            </Badge>
          </div>
          <Separator orientation="vertical" className="hidden h-6 sm:block" />
          <ModeToggle />
        </header>
        <main className="flex-1 overflow-auto p-4 md:p-8">
          <ErrorBoundary title="Page error">
            <Outlet key={location.pathname} />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
