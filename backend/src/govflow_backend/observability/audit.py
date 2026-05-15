"""Structured audit records for AI-facing routes."""

from __future__ import annotations

import hashlib
from typing import Any

from starlette.requests import Request

from govflow_backend.core.logging import get_logger
from govflow_backend.responsible_ai.schema import ResponsibleAiYaml

_audit = get_logger("govflow_backend.ai_audit")


def _preview(text: str, max_len: int) -> str:
    if max_len <= 0:
        return ""
    t = text.strip()
    if len(t) <= max_len:
        return t
    return t[:max_len] + "…"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def log_ai_audit(
    *,
    request: Request,
    action: str,
    duration_ms: float,
    ra: ResponsibleAiYaml,
    guardrails: dict[str, Any],
    blocked: bool,
    observability: dict[str, Any] | None = None,
    input_text: str | None = None,
    output_text: str | None = None,
) -> None:
    if not ra.audit.enabled:
        return

    corr = getattr(request.state, "correlation_id", None) or "-"
    client = request.client.host if request.client else "-"

    payload: dict[str, Any] = {
        "audit_kind": "ai_audit",
        "action": action,
        "correlation_id": corr,
        "client_host": client,
        "path": str(request.url.path),
        "duration_ms": round(duration_ms, 3),
        "guardrails": guardrails,
        "blocked": blocked,
    }
    if observability is not None:
        payload["observability_totals"] = (observability or {}).get("totals", {})

    if input_text is not None:
        payload["input_sha256"] = _sha256(input_text)
        payload["input_preview"] = _preview(input_text, ra.audit.max_prompt_chars_logged)
        payload["input_chars"] = len(input_text)
    if output_text is not None:
        payload["output_sha256"] = _sha256(output_text)
        payload["output_preview"] = _preview(output_text, ra.audit.max_response_chars_logged)
        payload["output_chars"] = len(output_text)

    _audit.info("ai_interaction", **payload)
