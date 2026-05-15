"""One-off smoke check: start uvicorn briefly and hit /health/live (run from repo CI or local)."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = root / "config"
    env = dict(os.environ)
    env.update(
        {
            "GOVFLOW_ENV": "development",
            "GOVFLOW_CONFIG_DIR": str(cfg),
            "GOVFLOW_SAMPLE_DATA_DIR": str(root / "sample_data"),
            "GOVFLOW_LOG_DIR": str(root / "logs"),
            "GOVFLOW_BACKEND_HOST": "127.0.0.1",
            "GOVFLOW_BACKEND_PORT": "8055",
            "GOVFLOW_BACKEND_RELOAD": "false",
            "GOVFLOW_BACKEND_ROOT_PATH": "",
            "GOVFLOW_BACKEND_CORS_ORIGINS": "http://localhost:5173",
            "GOVFLOW_LOG_LEVEL": "INFO",
            "GOVFLOW_LOG_JSON": "false",
            "GOVFLOW_LOG_UVICORN_ACCESS": "false",
            "GOVFLOW_HTTP_ACCESS_LOG_ENABLED": "false",
            "GOVFLOW_CORRELATION_ID_REQUEST_HEADER": "X-Correlation-ID",
            "GOVFLOW_CORRELATION_ID_RESPONSE_HEADER": "X-Correlation-ID",
            "GOVFLOW_SECURITY_TRUSTED_HOSTS": "",
            "GOVFLOW_SECURITY_ENABLE_HSTS": "false",
            "GOVFLOW_SECURITY_HSTS_MAX_AGE_SECONDS": "0",
            "GOVFLOW_SECURITY_ENABLE_FRAME_OPTIONS": "true",
            "GOVFLOW_SECURITY_FRAME_OPTIONS_VALUE": "DENY",
            "GOVFLOW_SECURITY_ENABLE_CONTENT_TYPE_OPTIONS": "true",
            "GOVFLOW_SECURITY_REFERRER_POLICY": "strict-origin-when-cross-origin",
            "GOVFLOW_SECURITY_PERMISSIONS_POLICY": "",
            "GOVFLOW_LANGGRAPH_THREAD_ID_PREFIX": "smoke",
        },
    )
    backend = root / "backend"
    p = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "govflow_backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8055",
        ],
        cwd=str(backend),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for _ in range(50):
            time.sleep(0.1)
            try:
                with urllib.request.urlopen("http://127.0.0.1:8055/health/live", timeout=1) as r:
                    body = r.read().decode().strip()
                print(f"health_ok status={r.status} body={body}")
                return
            except urllib.error.URLError:
                continue
        err = p.stderr.read() if p.stderr else ""
        raise SystemExit(f"server did not become ready: {err}")
    finally:
        p.terminate()
        p.wait(timeout=5)


if __name__ == "__main__":
    main()
