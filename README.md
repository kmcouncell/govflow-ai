# GovFlow AI

Monorepo: FastAPI + LangGraph backend, React + Vite frontend. See `docs/overview.md`.

## Quick start

```bash
cp .env.example .env
cd backend && uv sync --extra dev && uv run pytest
cd ../frontend && npm install && npm run test
```

Run API from repo root (so `GOVFLOW_CONFIG_DIR=config` resolves):

```bash
cd backend && uv run uvicorn govflow_backend.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend (loads env from repo root):

```bash
cd frontend && npm run dev
```
