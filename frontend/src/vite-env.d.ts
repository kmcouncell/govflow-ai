/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GOVFLOW_API_BASE_URL: string;
  readonly VITE_GOVFLOW_APP_NAME: string;
  readonly VITE_GOVFLOW_ENV: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
