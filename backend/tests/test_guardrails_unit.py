from __future__ import annotations

from pathlib import Path

from govflow_backend.responsible_ai.guardrails import (
    apply_text_guardrails,
    validate_user_input_text,
)
from govflow_backend.responsible_ai.loader import load_responsible_ai_config
from govflow_backend.responsible_ai.schema import GuardrailsConfig


def _base_guardrails() -> GuardrailsConfig:
    repo = Path(__file__).resolve().parents[2]
    cfg = load_responsible_ai_config(
        config_dir=repo / "config",
        environment="development",
    )
    return cfg.guardrails


def test_pii_ssn_redacted_in_redact_mode() -> None:
    g = _base_guardrails()
    text = "Contact 123-45-6789 for details."
    out = apply_text_guardrails(text, g)
    assert not out.blocked
    assert "REDACTED-SSN" in out.text
    assert "ssn_redacted" in out.flags


def test_output_blocked_secret_pattern() -> None:
    g = _base_guardrails()
    out = apply_text_guardrails("Here is my password: supersecretvalue", g)
    assert out.blocked
    assert "blocked_pattern" in "".join(out.flags)


def test_hallucination_flag_long_response() -> None:
    g = _base_guardrails()
    short = "x" * 400 + " guaranteed accurate"
    o1 = apply_text_guardrails(short, g)
    assert "potential_overconfident_language" not in o1.flags
    long = "x" * 520 + " guaranteed accurate"
    o2 = apply_text_guardrails(long, g)
    assert "potential_overconfident_language" in o2.flags


def test_input_blocked_custom_regex() -> None:
    base = _base_guardrails()
    iv = base.input_validation.model_copy(update={"blocked_regex": [r"(?i)drop\s+table"]})
    g = base.model_copy(update={"input_validation": iv})
    res = validate_user_input_text("Please DROP TABLE users;", g)
    assert res.blocked


def test_cui_block_when_configured() -> None:
    base = _base_guardrails()
    cui = base.cui_pii.model_copy(
        update={"block_if_cui_markers": True, "cui_marker_substrings": ["CUI//"]},
    )
    g = base.model_copy(update={"cui_pii": cui})
    out = apply_text_guardrails("This line has CUI//SP-EMAIL marker.", g)
    assert out.blocked
