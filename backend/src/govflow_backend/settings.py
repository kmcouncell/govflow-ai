"""Pydantic v2 settings: environment variables and optional env-specific .env files."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, computed_field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from pydantic_settings.sources import DotEnvSettingsSource

from govflow_backend.exceptions import ConfigurationError

EnvironmentName = Literal["development", "staging", "production"]


def _prime_env_from_dotenv() -> None:
    """Load base `.env` into the process so `GOVFLOW_ENV` is visible before layered files."""

    base = Path(".env")
    if base.is_file():
        load_dotenv(base, override=False)


_prime_env_from_dotenv()


def _split_csv(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return [v.strip() for v in value if str(v).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


class GovFlowSettings(BaseSettings):
    """All runtime configuration originates from the environment (see root `.env.example`)."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: EnvironmentName = Field(
        validation_alias=AliasChoices("GOVFLOW_ENV", "ENVIRONMENT"),
    )
    config_dir: Path = Field(validation_alias="GOVFLOW_CONFIG_DIR")
    sample_data_dir: Path = Field(validation_alias="GOVFLOW_SAMPLE_DATA_DIR")
    log_dir: Path = Field(validation_alias="GOVFLOW_LOG_DIR")

    backend_host: str = Field(validation_alias="GOVFLOW_BACKEND_HOST")
    backend_port: int = Field(validation_alias="GOVFLOW_BACKEND_PORT", ge=1, le=65535)
    backend_reload: bool = Field(validation_alias="GOVFLOW_BACKEND_RELOAD")
    backend_root_path: str = Field(validation_alias="GOVFLOW_BACKEND_ROOT_PATH")
    backend_cors_origins_csv: str = Field(validation_alias="GOVFLOW_BACKEND_CORS_ORIGINS")

    log_level: str = Field(validation_alias="GOVFLOW_LOG_LEVEL")
    log_json: bool = Field(validation_alias="GOVFLOW_LOG_JSON")

    openai_api_key: str | None = Field(default=None, validation_alias="GOVFLOW_OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, validation_alias="GOVFLOW_OPENAI_BASE_URL")
    openai_model: str | None = Field(default=None, validation_alias="GOVFLOW_OPENAI_MODEL")

    langgraph_checkpoint_dir: str | None = Field(
        default=None,
        validation_alias="GOVFLOW_LANGGRAPH_CHECKPOINT_DIR",
    )
    langgraph_thread_id_prefix: str = Field(validation_alias="GOVFLOW_LANGGRAPH_THREAD_ID_PREFIX")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_config_dir(self) -> Path:
        path = self.config_dir.expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_sample_data_dir(self) -> Path:
        path = self.sample_data_dir.expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_log_dir(self) -> Path:
        path = self.log_dir.expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve()

    def model_post_init(self, __context: object) -> None:
        if not self.resolved_config_dir.is_dir():
            raise ConfigurationError(
                f"GOVFLOW_CONFIG_DIR is not a directory: {self.resolved_config_dir}",
            )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def backend_cors_origins(self) -> list[str]:
        return _split_csv(self.backend_cors_origins_csv)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Layer optional `.env.<GOVFLOW_ENV>` after base `.env` (primed on import)."""

        from os import getenv

        env_name = getenv("GOVFLOW_ENV") or getenv("ENVIRONMENT")
        paths: list[str] = []
        base = Path(".env")
        if base.is_file():
            paths.append(str(base))
        if env_name:
            overlay = Path(f".env.{env_name}")
            if overlay.is_file():
                paths.append(str(overlay))
        dotenv = DotEnvSettingsSource(
            settings_cls,
            env_file=tuple(paths) if paths else None,
            env_file_encoding="utf-8",
        )
        return init_settings, env_settings, dotenv, file_secret_settings


@lru_cache
def get_settings() -> GovFlowSettings:
    """Cached settings singleton for import-time access patterns."""

    return GovFlowSettings()  # type: ignore[call-arg]
