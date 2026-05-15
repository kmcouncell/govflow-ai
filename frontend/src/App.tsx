import { Button } from "@/components/ui/button";
import { getPublicEnv } from "@/lib/env";

export default function App() {
  const env = getPublicEnv();
  return (
    <main className="min-h-dvh flex flex-col items-center justify-center gap-6 p-8">
      <div className="max-w-xl space-y-2 text-center">
        <h1 className="text-3xl font-semibold tracking-tight">{env.appName}</h1>
        <p className="text-muted-foreground text-sm">
          Environment: {env.environment}. API base URL is loaded from{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">VITE_GOVFLOW_API_BASE_URL</code>.
        </p>
      </div>
      <Button asChild variant="outline">
        <a href={`${env.apiBaseUrl}/health/live`} rel="noreferrer" target="_blank">
          Open backend health check
        </a>
      </Button>
    </main>
  );
}
