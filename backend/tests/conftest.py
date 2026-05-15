"""Pytest: set process env before any `govflow_backend` imports (see collection order)."""

from __future__ import annotations

import os
from pathlib import Path

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
    os.environ["GOVFLOW_LANGGRAPH_THREAD_ID_PREFIX"] = "test"


_install_test_env()

from govflow_backend.settings import get_settings  # noqa: E402

get_settings.cache_clear()
