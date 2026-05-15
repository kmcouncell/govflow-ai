# GovFlow AI — Backend

Python 3.12, FastAPI, LangGraph. Environment variables (repository root `.env.example`), YAML under `config/`, and `govflow_backend.core.config.GovFlowSettings`. Logging, correlation IDs, and security middleware live under `govflow_backend.core`.

## Commands

```bash
cd backend
uv sync --extra dev
uv run pytest
# from repository root with `.env` present, or export GOVFLOW_* variables:
uv run uvicorn govflow_backend.main:app --reload --host 127.0.0.1 --port 8000
```
