/** Typed accessors for Vite `import.meta.env` (values come from root `.env`). */

export type PublicEnv = {
  apiBaseUrl: string;
  appName: string;
  environment: string;
  graphStreamPath: string;
  featureAssistant: boolean;
  featureWorkflow: boolean;
};

function readRequired(key: keyof ImportMetaEnv): string {
  const value = import.meta.env[key];
  if (value === undefined || value === null || String(value).trim() === "") {
    throw new Error(`Missing required public env: ${String(key)}`);
  }
  return String(value);
}

function readOptionalBool(key: keyof ImportMetaEnv, defaultValue: boolean): boolean {
  const value = import.meta.env[key];
  if (value === undefined || value === null || String(value).trim() === "") {
    return defaultValue;
  }
  const normalized = String(value).trim().toLowerCase();
  return normalized === "true" || normalized === "1" || normalized === "yes";
}

export function getPublicEnv(): PublicEnv {
  return {
    apiBaseUrl: readRequired("VITE_GOVFLOW_API_BASE_URL"),
    appName: readRequired("VITE_GOVFLOW_APP_NAME"),
    environment: readRequired("VITE_GOVFLOW_ENV"),
    graphStreamPath: readRequired("VITE_GOVFLOW_GRAPH_STREAM_PATH"),
    featureAssistant: readOptionalBool("VITE_GOVFLOW_FEATURE_ASSISTANT", true),
    featureWorkflow: readOptionalBool("VITE_GOVFLOW_FEATURE_WORKFLOW", true),
  };
}
