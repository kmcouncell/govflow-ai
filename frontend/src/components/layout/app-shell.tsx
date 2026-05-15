import * as React from "react";
import { Activity, LayoutDashboard, MessageSquare, Shield } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { ModeToggle } from "@/components/mode-toggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { getPublicEnv } from "@/lib/env";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/assistant", label: "Assistant", icon: MessageSquare, end: false },
];

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1 px-2">
      {nav.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-primary/10 text-primary dark:bg-primary/20"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
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

  return (
    <div className="flex min-h-dvh w-full bg-background">
      <aside className="hidden w-60 shrink-0 border-r bg-card/40 backdrop-blur-sm md:flex md:flex-col">
        <div className="flex h-14 items-center gap-2 border-b px-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-xs font-bold text-primary-foreground">
            GF
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold leading-tight">{env.appName}</p>
            <p className="text-xs text-muted-foreground">Operations console</p>
          </div>
        </div>
        <div className="flex-1 py-4">
          <NavItems />
        </div>
        <div className="border-t p-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Shield className="h-3.5 w-3.5" />
            <span>Guardrails & audit-ready</span>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 flex h-14 items-center gap-3 border-b bg-background/80 px-4 backdrop-blur-md">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="sm" className="md:hidden" aria-label="Open menu">
                <LayoutDashboard className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent className="w-64 border-r p-0">
              <SheetHeader className="border-b p-4 text-left">
                <SheetTitle className="text-base">{env.appName}</SheetTitle>
              </SheetHeader>
              <div className="py-4">
                <NavItems onNavigate={() => setMobileOpen(false)} />
              </div>
            </SheetContent>
          </Sheet>
          <div className="flex min-w-0 flex-1 items-center gap-2">
            <Activity className="hidden h-4 w-4 text-muted-foreground sm:block" />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">Mission overview</p>
              <p className="truncate text-xs text-muted-foreground">
                Environment: <span className="font-mono">{env.environment}</span>
              </p>
            </div>
          </div>
          <Badge variant="outline" className="hidden sm:inline-flex">
            API {env.apiBaseUrl.replace(/^https?:\/\//, "")}
          </Badge>
          <Separator orientation="vertical" className="hidden h-6 sm:block" />
          <ModeToggle />
        </header>
        <main className="flex-1 overflow-auto p-4 md:p-6">
          <Outlet key={location.pathname} />
        </main>
      </div>
    </div>
  );
}
