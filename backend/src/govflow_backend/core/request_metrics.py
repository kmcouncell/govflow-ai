"""Per-request timing headers for AI and general routes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Adds wall-time headers for observability and downstream monitoring."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        t0 = perf_counter()
        response = await call_next(request)
        elapsed_ms = (perf_counter() - t0) * 1000.0
        path = request.url.path
        if path.startswith("/v1/graph") or path.startswith("/v1/rag"):
            response.headers["X-Govflow-AI-Route-Latency-Ms"] = f"{elapsed_ms:.2f}"
        response.headers["X-Govflow-Request-Duration-Ms"] = f"{elapsed_ms:.2f}"
        return response
