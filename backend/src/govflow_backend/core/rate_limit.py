"""In-memory sliding-window rate limiting for AI routes."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from govflow_backend.responsible_ai.schema import ResponsibleAiYaml


def _client_key(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _is_ai_path(path: str) -> bool:
    return path.startswith("/v1/graph") or path.startswith("/v1/rag/query")


def _is_health(path: str) -> bool:
    return path.startswith("/health")


class SlidingWindowRateLimiter:
    """Sufficient for asyncio single-threaded event loop."""

    def __init__(self) -> None:
        self._hits: dict[tuple[str, str], list[float]] = defaultdict(list)

    def allow(self, *, key: str, bucket: str, limit: int, window_seconds: float) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        slot = (key, bucket)
        seq = [t for t in self._hits[slot] if t >= cutoff]
        if len(seq) >= limit:
            self._hits[slot] = seq
            return False
        seq.append(now)
        self._hits[slot] = seq
        return True


_limiter = SlidingWindowRateLimiter()


def reset_rate_limit_counters() -> None:
    """Clear in-memory counters (for tests)."""

    _limiter._hits.clear()


def rate_limit_check(request: Request, ra: ResponsibleAiYaml) -> Response | None:
    """Return a 429 JSONResponse if limited, else None."""

    if not ra.rate_limiting.enabled:
        return None
    path = request.url.path
    if _is_health(path):
        return None

    key = _client_key(request)
    window = float(ra.rate_limiting.window_seconds)
    if _is_ai_path(path):
        lim = ra.rate_limiting.ai_route_requests_per_window
        bucket = "ai"
    else:
        lim = ra.rate_limiting.default_requests_per_window
        bucket = "default"

    if not _limiter.allow(key=key, bucket=bucket, limit=lim, window_seconds=window):
        return JSONResponse(
            status_code=429,
            content={
                "detail": "rate_limited",
                "message": "Too many requests; try again later.",
                "window_seconds": ra.rate_limiting.window_seconds,
            },
        )
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """429 JSON responses when in-memory limits are exceeded."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        ra = getattr(request.app.state, "responsible_ai", None)
        if isinstance(ra, ResponsibleAiYaml):
            blocked = rate_limit_check(request, ra)
            if blocked is not None:
                return blocked
        return await call_next(request)
