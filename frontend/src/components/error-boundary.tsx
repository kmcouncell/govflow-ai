import { AlertTriangle } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type ErrorBoundaryProps = {
  children: React.ReactNode;
  title?: string;
};

type ErrorBoundaryState = {
  error: Error | null;
};

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  private reset = (): void => {
    this.setState({ error: null });
  };

  override render(): React.ReactNode {
    const { error } = this.state;
    if (error) {
      return (
        <div className="mx-auto flex max-w-lg flex-col gap-4 p-6">
          <Card className="border-destructive/40 bg-destructive/5">
            <CardHeader>
              <div className="flex items-center gap-2 text-destructive">
                <AlertTriangle className="h-5 w-5 shrink-0" />
                <CardTitle>{this.props.title ?? "Something went wrong"}</CardTitle>
              </div>
              <CardDescription>
                The page hit an unexpected error. You can retry or return to the dashboard.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <pre className="max-h-40 overflow-auto rounded-md border bg-muted/50 p-3 text-xs leading-relaxed">
                {error.message}
              </pre>
              <Button type="button" onClick={this.reset}>
                Try again
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }
    return this.props.children;
  }
}
