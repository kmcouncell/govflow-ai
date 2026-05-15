/** Typed accessors for Vite `import.meta.env` (values come from root `.env`). */

export type PublicEnv = {
  apiBaseUrl: string;
  appName: string;
  environment: string;
};

function readRequired(key: keyof ImportMetaEnv): string {
  const value = import.meta.env[key];
  if (value === undefined || value === null || String(value).trim() === "") {
    throw new Error(`Missing required public env: ${String(key)}`);
  }
  return String(value);
}

export function getPublicEnv(): PublicEnv {
  return {
    apiBaseUrl: readRequired("VITE_GOVFLOW_API_BASE_URL"),
    appName: readRequired("VITE_GOVFLOW_APP_NAME"),
    environment: readRequired("VITE_GOVFLOW_ENV"),
  };
}
