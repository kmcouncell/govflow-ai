"""Security-related middleware (trusted hosts, browser hardening headers)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from govflow_backend.core.config import GovFlowSettings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Applies configurable response headers driven entirely by `GovFlowSettings`."""

    def __init__(self, app, settings: GovFlowSettings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        s = self._settings

        if s.security_enable_hsts and s.security_hsts_max_age_seconds > 0:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={s.security_hsts_max_age_seconds}; includeSubDomains"
            )

        if s.security_enable_frame_options and s.security_frame_options_value.strip():
            response.headers["X-Frame-Options"] = s.security_frame_options_value.strip()

        if s.security_enable_content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"

        if s.security_referrer_policy.strip():
            response.headers["Referrer-Policy"] = s.security_referrer_policy.strip()

        if s.security_permissions_policy.strip():
            response.headers["Permissions-Policy"] = s.security_permissions_policy.strip()

        rai = getattr(request.app.state, "responsible_ai", None)
        if rai is not None:
            hs = rai.http_security
            if hs.content_security_policy.strip():
                response.headers["Content-Security-Policy"] = hs.content_security_policy.strip()
            if hs.cross_origin_opener_policy.strip():
                response.headers["Cross-Origin-Opener-Policy"] = (
                    hs.cross_origin_opener_policy.strip()
                )
            if hs.cross_origin_resource_policy.strip():
                response.headers["Cross-Origin-Resource-Policy"] = (
                    hs.cross_origin_resource_policy.strip()
                )
            if hs.permissions_policy_extra.strip():
                existing = response.headers.get("Permissions-Policy", "")
                extra = hs.permissions_policy_extra.strip()
                response.headers["Permissions-Policy"] = (
                    f"{existing}, {extra}" if existing else extra
                )

        return response


def install_security_middleware(app: FastAPI, settings: GovFlowSettings) -> None:
    """Register security layers.

    Middleware is wrapped in registration order: the **last** registration is outermost
    on the request path, so trusted hosts are registered after security headers.
    """

    app.add_middleware(SecurityHeadersMiddleware, settings=settings)
    if settings.security_trusted_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.security_trusted_hosts)
