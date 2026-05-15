"""Complete application settings from environment (see repository root `.env.example`)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, computed_field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from pydantic_settings.sources import DotEnvSettingsSource

from govflow_backend.exceptions import ConfigurationError

EnvironmentName = Literal["development", "staging", "production"]


def _walk_up_for(start: Path, filename: str) -> Path | None:
    for directory in [start, *start.parents]:
        candidate = directory / filename
        if candidate.is_file():
            return candidate
    return None


def _find_env_file(filename: str) -> Path | None:
    """Resolve `.env` when the process CWD is not the repository root.

    Typical case: `uv run --directory backend`.
    """

    hit = _walk_up_for(Path.cwd().resolve(), filename)
    if hit is not None:
        return hit
    return _walk_up_for(Path(__file__).resolve().parent, filename)


def _settings_anchor_directory() -> Path:
    """Anchor directory for resolving relative `GOVFLOW_*` paths when `.env` is at repo root."""

    env_file = _find_env_file(".env")
    if env_file is not None:
        return env_file.parent.resolve()
    return Path.cwd().resolve()


def _prime_env_from_dotenv() -> None:
    """Load base `.env` so `GOVFLOW_ENV` exists before optional `.env.<env>` layering."""

    base = _find_env_file(".env")
    if base is not None:
        load_dotenv(base, override=False)


_prime_env_from_dotenv()


def _split_csv(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


class GovFlowSettings(BaseSettings):
    """All runtime configuration is supplied via environment variables."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- runtime / paths ---
    environment: EnvironmentName = Field(
        validation_alias=AliasChoices("GOVFLOW_ENV", "ENVIRONMENT"),
    )
    config_dir: Path = Field(validation_alias="GOVFLOW_CONFIG_DIR")
    sample_data_dir: Path = Field(validation_alias="GOVFLOW_SAMPLE_DATA_DIR")
    log_dir: Path = Field(validation_alias="GOVFLOW_LOG_DIR")

    # --- HTTP server (uvicorn) ---
    backend_host: str = Field(validation_alias="GOVFLOW_BACKEND_HOST")
    backend_port: int = Field(validation_alias="GOVFLOW_BACKEND_PORT", ge=1, le=65535)
    backend_reload: bool = Field(validation_alias="GOVFLOW_BACKEND_RELOAD")
    backend_root_path: str = Field(validation_alias="GOVFLOW_BACKEND_ROOT_PATH")
    backend_cors_origins_csv: str = Field(validation_alias="GOVFLOW_BACKEND_CORS_ORIGINS")

    # --- logging ---
    log_level: str = Field(validation_alias="GOVFLOW_LOG_LEVEL")
    log_json: bool = Field(validation_alias="GOVFLOW_LOG_JSON")
    log_uvicorn_access: bool = Field(validation_alias="GOVFLOW_LOG_UVICORN_ACCESS")
    http_access_log_enabled: bool = Field(validation_alias="GOVFLOW_HTTP_ACCESS_LOG_ENABLED")

    # --- correlation / tracing ---
    correlation_id_request_header: str = Field(
        validation_alias="GOVFLOW_CORRELATION_ID_REQUEST_HEADER",
    )
    correlation_id_response_header: str = Field(
        validation_alias="GOVFLOW_CORRELATION_ID_RESPONSE_HEADER",
    )

    # --- security ---
    security_trusted_hosts_csv: str = Field(validation_alias="GOVFLOW_SECURITY_TRUSTED_HOSTS")
    security_enable_hsts: bool = Field(validation_alias="GOVFLOW_SECURITY_ENABLE_HSTS")
    security_hsts_max_age_seconds: int = Field(
        validation_alias="GOVFLOW_SECURITY_HSTS_MAX_AGE_SECONDS",
        ge=0,
    )
    security_enable_frame_options: bool = Field(
        validation_alias="GOVFLOW_SECURITY_ENABLE_FRAME_OPTIONS",
    )
    security_frame_options_value: str = Field(
        validation_alias="GOVFLOW_SECURITY_FRAME_OPTIONS_VALUE",
    )
    security_enable_content_type_options: bool = Field(
        validation_alias="GOVFLOW_SECURITY_ENABLE_CONTENT_TYPE_OPTIONS",
    )
    security_referrer_policy: str = Field(validation_alias="GOVFLOW_SECURITY_REFERRER_POLICY")
    security_permissions_policy: str = Field(
        validation_alias="GOVFLOW_SECURITY_PERMISSIONS_POLICY",
    )

    # --- LLM (optional) ---
    openai_api_key: str | None = Field(default=None, validation_alias="GOVFLOW_OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, validation_alias="GOVFLOW_OPENAI_BASE_URL")
    openai_model: str | None = Field(default=None, validation_alias="GOVFLOW_OPENAI_MODEL")

    # --- LangGraph (optional) ---
    langgraph_checkpoint_dir: str | None = Field(
        default=None,
        validation_alias="GOVFLOW_LANGGRAPH_CHECKPOINT_DIR",
    )
    langgraph_thread_id_prefix: str = Field(validation_alias="GOVFLOW_LANGGRAPH_THREAD_ID_PREFIX")

    # --- feature flags (optional; when unset, YAML `features.*_api_enabled` applies) ---
    feature_rag_api_enabled: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("GOVFLOW_FEATURE_RAG_API_ENABLED"),
    )
    feature_graph_api_enabled: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("GOVFLOW_FEATURE_GRAPH_API_ENABLED"),
    )

    # --- RAG / vector ---
    rag_vector_backend: str = Field(validation_alias="GOVFLOW_RAG_VECTOR_BACKEND")
    rag_chroma_persist_directory: Path = Field(
        validation_alias="GOVFLOW_RAG_CHROMA_PERSIST_DIRECTORY",
    )
    rag_pg_dsn: str = Field(validation_alias="GOVFLOW_RAG_PG_DSN")
    rag_collection_name: str = Field(validation_alias="GOVFLOW_RAG_COLLECTION_NAME")
    rag_embedding_model: str = Field(validation_alias="GOVFLOW_RAG_EMBEDDING_MODEL")
    rag_embedding_dimensions: int = Field(
        validation_alias="GOVFLOW_RAG_EMBEDDING_DIMENSIONS",
        ge=8,
        le=8192,
    )
    rag_use_fake_embeddings: bool = Field(validation_alias="GOVFLOW_RAG_USE_FAKE_EMBEDDINGS")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_rag_chroma_dir(self) -> Path:
        path = self.rag_chroma_persist_directory.expanduser()
        if not path.is_absolute():
            path = _settings_anchor_directory() / path
        return path.resolve()

    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, value: str) -> str:
        return value.strip().upper()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_config_dir(self) -> Path:
        path = self.config_dir.expanduser()
        if not path.is_absolute():
            path = _settings_anchor_directory() / path
        return path.resolve()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_sample_data_dir(self) -> Path:
        path = self.sample_data_dir.expanduser()
        if not path.is_absolute():
            path = _settings_anchor_directory() / path
        return path.resolve()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_log_dir(self) -> Path:
        path = self.log_dir.expanduser()
        if not path.is_absolute():
            path = _settings_anchor_directory() / path
        return path.resolve()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def backend_cors_origins(self) -> list[str]:
        return _split_csv(self.backend_cors_origins_csv)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def security_trusted_hosts(self) -> list[str]:
        return _split_csv(self.security_trusted_hosts_csv)

    def model_post_init(self, __context: object) -> None:
        if not self.resolved_config_dir.is_dir():
            raise ConfigurationError(
                f"GOVFLOW_CONFIG_DIR is not a directory: {self.resolved_config_dir}",
            )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        from os import getenv

        env_name = getenv("GOVFLOW_ENV") or getenv("ENVIRONMENT")
        paths: list[str] = []
        base = _find_env_file(".env")
        if base is not None:
            paths.append(str(base))
            if env_name:
                overlay = base.parent / f".env.{env_name}"
                if overlay.is_file():
                    paths.append(str(overlay))
        elif env_name:
            overlay_only = _find_env_file(f".env.{env_name}")
            if overlay_only is not None:
                paths.append(str(overlay_only))
        dotenv = DotEnvSettingsSource(
            settings_cls,
            env_file=tuple(paths) if paths else None,
            env_file_encoding="utf-8",
        )
        return init_settings, env_settings, dotenv, file_secret_settings


@lru_cache
def get_settings() -> GovFlowSettings:
    """Process-wide cached settings (clear in tests when environment changes)."""

    return GovFlowSettings()  # type: ignore[call-arg]


# Alias for readability in type hints
Settings = GovFlowSettings
