import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as React from "react";

function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
        refetchOnWindowFocus: true,
        staleTime: 30_000,
      },
      mutations: {
        retry: 0,
      },
    },
  });
}

export function GovflowQueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = React.useState(makeQueryClient);
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
