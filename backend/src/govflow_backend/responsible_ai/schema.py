"""Pydantic models for responsible AI YAML."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RateLimitingConfig(BaseModel):
    enabled: bool
    window_seconds: int = Field(ge=5, le=3600)
    default_requests_per_window: int = Field(ge=1, le=100_000)
    ai_route_requests_per_window: int = Field(ge=1, le=100_000)


class HttpSecurityExtraConfig(BaseModel):
    content_security_policy: str = ""
    cross_origin_opener_policy: str = ""
    cross_origin_resource_policy: str = ""
    permissions_policy_extra: str = ""


class AuditConfig(BaseModel):
    enabled: bool
    max_prompt_chars_logged: int = Field(ge=0, le=10_000)
    max_response_chars_logged: int = Field(ge=0, le=50_000)


class InputValidationConfig(BaseModel):
    enabled: bool
    max_request_chars: int = Field(ge=100, le=2_000_000)
    blocked_regex: list[str] = Field(default_factory=list)


class OutputValidationConfig(BaseModel):
    enabled: bool
    max_output_chars: int = Field(ge=100, le=2_000_000)
    blocked_regex: list[str] = Field(default_factory=list)


class CuiPiiConfig(BaseModel):
    enabled: bool
    mode: Literal["redact", "block", "log_only"] = "redact"
    redact_ssn: bool = True
    redact_email: bool = True
    redact_phone: bool = True
    block_if_cui_markers: bool = False
    cui_marker_substrings: list[str] = Field(default_factory=list)


class HallucinationDetectionConfig(BaseModel):
    enabled: bool
    min_assistant_chars: int = Field(ge=0, le=1_000_000)
    risky_phrases: list[str] = Field(default_factory=list)
    block_on_risky_phrase: bool = False


class GuardrailsConfig(BaseModel):
    input_validation: InputValidationConfig
    output_validation: OutputValidationConfig
    cui_pii: CuiPiiConfig
    hallucination_detection: HallucinationDetectionConfig


class ResponsibleAiYaml(BaseModel):
    version: int = Field(ge=1)
    rate_limiting: RateLimitingConfig
    http_security: HttpSecurityExtraConfig
    audit: AuditConfig
    guardrails: GuardrailsConfig
