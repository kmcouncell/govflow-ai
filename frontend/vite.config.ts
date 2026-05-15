/// <reference types="vitest/config" />

import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(__dirname, ".."), "");
  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      port: Number(env.FRONTEND_DEV_PORT || 5173),
    },
    envDir: path.resolve(__dirname, ".."),
    envPrefix: ["VITE_"],
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      env: {
        VITE_GOVFLOW_API_BASE_URL: "http://localhost:8000",
        VITE_GOVFLOW_APP_NAME: "GovFlow AI",
        VITE_GOVFLOW_ENV: "test",
        VITE_GOVFLOW_GRAPH_STREAM_PATH: "/v1/graph/stream",
      },
    },
  };
});
