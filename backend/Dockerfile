# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS deps
WORKDIR /app/backend
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY backend/pyproject.toml backend/README.md ./
COPY backend/src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

FROM python:3.12-slim-bookworm AS runtime
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 govflow \
    && useradd --uid 10001 --gid govflow --system --create-home --shell /usr/sbin/nologin govflow

ENV PYTHONPATH=/app/backend/src
ENV PATH="/app/backend/.venv/bin:${PATH}"
ENV GOVFLOW_BACKEND_HOST=0.0.0.0
ENV GOVFLOW_BACKEND_PORT=8000

COPY --from=deps /app/backend/.venv /app/backend/.venv
COPY backend /app/backend
COPY config /app/config
COPY sample_data /app/sample_data

RUN mkdir -p /app/logs /app/data/chroma \
    && chown -R govflow:govflow /app

USER govflow
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health/live -o /dev/null

CMD ["sh", "-c", "cd /app/backend && exec uvicorn govflow_backend.main:app --host ${GOVFLOW_BACKEND_HOST} --port ${GOVFLOW_BACKEND_PORT}"]
