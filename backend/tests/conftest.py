"""Pytest: set process env before any `govflow_backend` imports (see collection order)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_DIR = _REPO_ROOT / "config"


def _install_test_env() -> None:
    os.environ["GOVFLOW_ENV"] = "development"
    os.environ["GOVFLOW_CONFIG_DIR"] = str(_CONFIG_DIR)
    os.environ["GOVFLOW_SAMPLE_DATA_DIR"] = str(_REPO_ROOT / "sample_data")
    os.environ["GOVFLOW_LOG_DIR"] = str(_REPO_ROOT / "logs")
    os.environ["GOVFLOW_BACKEND_HOST"] = "127.0.0.1"
    os.environ["GOVFLOW_BACKEND_PORT"] = "8000"
    os.environ["GOVFLOW_BACKEND_RELOAD"] = "false"
    os.environ["GOVFLOW_BACKEND_ROOT_PATH"] = ""
    os.environ["GOVFLOW_BACKEND_CORS_ORIGINS"] = "http://localhost:5173"
    os.environ["GOVFLOW_LOG_LEVEL"] = "INFO"
    os.environ["GOVFLOW_LOG_JSON"] = "false"
    os.environ["GOVFLOW_LOG_UVICORN_ACCESS"] = "false"
    os.environ["GOVFLOW_HTTP_ACCESS_LOG_ENABLED"] = "false"
    os.environ["GOVFLOW_CORRELATION_ID_REQUEST_HEADER"] = "X-Correlation-ID"
    os.environ["GOVFLOW_CORRELATION_ID_RESPONSE_HEADER"] = "X-Correlation-ID"
    os.environ["GOVFLOW_SECURITY_TRUSTED_HOSTS"] = ""
    os.environ["GOVFLOW_SECURITY_ENABLE_HSTS"] = "false"
    os.environ["GOVFLOW_SECURITY_HSTS_MAX_AGE_SECONDS"] = "0"
    os.environ["GOVFLOW_SECURITY_ENABLE_FRAME_OPTIONS"] = "true"
    os.environ["GOVFLOW_SECURITY_FRAME_OPTIONS_VALUE"] = "DENY"
    os.environ["GOVFLOW_SECURITY_ENABLE_CONTENT_TYPE_OPTIONS"] = "true"
    os.environ["GOVFLOW_SECURITY_REFERRER_POLICY"] = "strict-origin-when-cross-origin"
    os.environ["GOVFLOW_SECURITY_PERMISSIONS_POLICY"] = ""
    os.environ["GOVFLOW_RAG_VECTOR_BACKEND"] = "chroma"
    os.environ["GOVFLOW_RAG_CHROMA_PERSIST_DIRECTORY"] = str(
        _REPO_ROOT / "backend" / ".pytest_chroma_data",
    )
    os.environ["GOVFLOW_RAG_PG_DSN"] = ""
    os.environ["GOVFLOW_RAG_COLLECTION_NAME"] = "pytest-rag"
    os.environ["GOVFLOW_RAG_EMBEDDING_MODEL"] = "text-embedding-3-small"
    os.environ["GOVFLOW_RAG_EMBEDDING_DIMENSIONS"] = "256"
    os.environ["GOVFLOW_RAG_USE_FAKE_EMBEDDINGS"] = "true"
    os.environ["GOVFLOW_RAG_SOURCE_DIR"] = str(_REPO_ROOT / "sample_data" / "rag_docs")
    os.environ["GOVFLOW_RAG_SINGLE_FILE"] = ""
    os.environ["GOVFLOW_LANGGRAPH_THREAD_ID_PREFIX"] = "test"
    Path(os.environ["GOVFLOW_RAG_CHROMA_PERSIST_DIRECTORY"]).mkdir(parents=True, exist_ok=True)


_install_test_env()

from govflow_backend.core.config import get_settings  # noqa: E402

get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_settings_cache_after_test() -> None:
    yield
    get_settings.cache_clear()
