# GovFlow AI — Overview

Federal Government Workflow AI Assistant monorepo.

## Layout

- `backend/` — Python 3.12, FastAPI, LangGraph, Pydantic Settings + YAML under `config/`.
- `frontend/` — React 19, TypeScript, Vite, Tailwind, shadcn/ui.
- `config/` — Non-secret defaults and environment overlays (`app.default.yaml`, `app.<env>.yaml`, etc.).
- `sample_data/` — Curated fixtures for demos and tests.

## Configuration

1. Copy `.env.example` to `.env` at the repository root.
2. Run the backend from the **repository root** so relative `GOVFLOW_CONFIG_DIR` resolves to `config/`, or set absolute paths in `.env`.
3. Optional: add `.env.development` (or matching `GOVFLOW_ENV`) for layered local overrides.

## Docker

```bash
docker compose up --build
```
