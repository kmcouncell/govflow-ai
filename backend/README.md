# GovFlow AI — Backend

Python 3.12, FastAPI, LangGraph. Configuration via environment variables, YAML under `config/`, and Pydantic Settings.

## Commands

```bash
cd backend
uv sync --extra dev
uv run pytest
uv run uvicorn govflow_backend.main:app --reload
```
