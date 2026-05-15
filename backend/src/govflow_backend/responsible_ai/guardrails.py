"""Heuristic guardrails: PII/CUI handling, output validation, hallucination-style flags."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from govflow_backend.core.logging import get_logger
from govflow_backend.responsible_ai.schema import GuardrailsConfig

log = get_logger(__name__)

_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b")


@dataclass
class GuardrailTextOutcome:
    text: str
    flags: list[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "flags": list(self.flags),
            "blocked": self.blocked,
            "block_reason": self.block_reason,
        }


def _compile_patterns(patterns: list[str]) -> list[re.Pattern[str]]:
    out: list[re.Pattern[str]] = []
    for p in patterns:
        try:
            out.append(re.compile(p))
        except re.error:
            log.warning("invalid_guardrail_regex", pattern=p)
    return out


def _redact_pii(text: str, g: GuardrailsConfig) -> tuple[str, list[str]]:
    flags: list[str] = []
    out = text
    c = g.cui_pii
    if c.redact_ssn and _SSN.search(out):
        out = _SSN.sub("[REDACTED-SSN]", out)
        flags.append("ssn_redacted")
    if c.redact_email and _EMAIL.search(out):
        out = _EMAIL.sub("[REDACTED-EMAIL]", out)
        flags.append("email_redacted")
    if c.redact_phone and _PHONE.search(out):
        out = _PHONE.sub("[REDACTED-PHONE]", out)
        flags.append("phone_redacted")
    return out, flags


def _detect_pii_presence(text: str, g: GuardrailsConfig) -> list[str]:
    hits: list[str] = []
    c = g.cui_pii
    if c.redact_ssn and _SSN.search(text):
        hits.append("ssn")
    if c.redact_email and _EMAIL.search(text):
        hits.append("email")
    if c.redact_phone and _PHONE.search(text):
        hits.append("phone")
    return hits


def _cui_markers_present(text: str, markers: list[str]) -> bool:
    low = text.lower()
    return any(m.lower() in low for m in markers if m.strip())


def apply_text_guardrails(text: str, g: GuardrailsConfig) -> GuardrailTextOutcome:
    """Run output-oriented checks on a single text blob."""

    flags: list[str] = []
    out = text
    ov = g.output_validation
    if ov.enabled:
        if len(out) > ov.max_output_chars:
            return GuardrailTextOutcome(
                text="",
                flags=["output_too_long"],
                blocked=True,
                block_reason="Response exceeded configured maximum length.",
            )
        for rx in _compile_patterns(ov.blocked_regex):
            if rx.search(out):
                return GuardrailTextOutcome(
                    text="",
                    flags=[f"blocked_pattern:{rx.pattern}"],
                    blocked=True,
                    block_reason="Response matched a blocked output pattern.",
                )

    cui = g.cui_pii
    markers = cui.cui_marker_substrings
    if cui.enabled and markers and _cui_markers_present(out, markers):
        flags.append("cui_marker_detected")
        if cui.block_if_cui_markers:
            return GuardrailTextOutcome(
                text="",
                flags=list(flags),
                blocked=True,
                block_reason="Controlled unclassified information markers detected in output.",
            )

    if cui.enabled:
        if cui.mode == "block":
            presence = _detect_pii_presence(out, g)
            if presence:
                return GuardrailTextOutcome(
                    text="",
                    flags=[f"pii:{p}" for p in presence],
                    blocked=True,
                    block_reason="Potential PII detected; blocking per policy.",
                )
        if cui.mode in ("redact", "log_only"):
            if cui.mode == "redact":
                out, pflags = _redact_pii(out, g)
                flags.extend(pflags)
            else:
                flags.extend(f"pii_present:{p}" for p in _detect_pii_presence(out, g))

    hd = g.hallucination_detection
    if hd.enabled and len(out) >= hd.min_assistant_chars:
        low = out.lower()
        for phrase in hd.risky_phrases:
            if phrase.lower() in low:
                flags.append("potential_overconfident_language")
                if hd.block_on_risky_phrase:
                    return GuardrailTextOutcome(
                        text="",
                        flags=list(flags),
                        blocked=True,
                        block_reason="Response matched risky phrase policy.",
                    )
                break

    return GuardrailTextOutcome(text=out, flags=flags, blocked=False)


def validate_user_input_text(text: str, g: GuardrailsConfig) -> GuardrailTextOutcome:
    """Validate inbound user text (questions, chat messages)."""

    iv = g.input_validation
    if not iv.enabled:
        return GuardrailTextOutcome(text=text, flags=[])

    if len(text) > iv.max_request_chars:
        return GuardrailTextOutcome(
            text="",
            flags=["input_too_long"],
            blocked=True,
            block_reason="Request exceeded maximum configured size.",
        )
    for rx in _compile_patterns(iv.blocked_regex):
        if rx.search(text):
            return GuardrailTextOutcome(
                text="",
                flags=[f"blocked_input_pattern:{rx.pattern}"],
                blocked=True,
                block_reason="Input matched a blocked pattern.",
            )
    return GuardrailTextOutcome(text=text, flags=[])


def collect_user_text_from_messages(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for m in messages:
        if m.get("type") == "human" or m.get("role") == "user":
            c = m.get("content", "")
            if isinstance(c, str):
                parts.append(c)
    return "\n".join(parts)


def apply_guardrails_to_assistant_messages(
    messages: list[dict[str, Any]],
    g: GuardrailsConfig,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return updated messages and aggregate guardrail summary."""

    aggregate_flags: list[str] = []
    any_blocked = False
    block_reason: str | None = None
    out: list[dict[str, Any]] = []

    for m in messages:
        if not isinstance(m, dict):
            continue
        mtype = str(m.get("type", ""))
        if mtype != "ai" and m.get("role") != "assistant":
            out.append(dict(m))
            continue
        content = m.get("content", "")
        if not isinstance(content, str):
            out.append(dict(m))
            continue
        res = apply_text_guardrails(content, g)
        aggregate_flags.extend(res.flags)
        if res.blocked:
            any_blocked = True
            block_reason = res.block_reason
            break
        mm = dict(m)
        mm["content"] = res.text
        if res.flags:
            extra = dict(mm.get("additional_kwargs") or {})
            extra["govflow_guardrails"] = res.flags
            mm["additional_kwargs"] = extra
        out.append(mm)

    summary = {
        "flags": sorted(set(aggregate_flags)),
        "blocked": any_blocked,
        "block_reason": block_reason,
    }
    return out, summary
