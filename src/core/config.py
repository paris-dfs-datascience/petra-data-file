from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PathsConfig(BaseModel):
    uploads_dir: str = "data/uploads"
    indexes_dir: str = "data/indexes"
    reports_dir: str = "data/reports"


class PdfConfig(BaseModel):
    dpi: int = 300
    image_format: str = "png"
    text_layout: bool = True
    text_x_density: float = 7.25
    text_y_density: float = 13.0


class VisionConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: str = "openai"
    model_id: str = "gpt-5.4"
    max_images_per_request: int = 10
    temperature: float = 0.1
    seed: int = 42
    max_completion_tokens: int = 1600
    image_detail: str = "high"
    concurrent_requests: int = 12
    global_max_concurrent: int = 24


class ReportConfig(BaseModel):
    include_thumbnails: bool = False


class AppYaml(BaseModel):
    app: dict = {"project_name": "petra-vision"}
    paths: PathsConfig = PathsConfig()
    pdf: PdfConfig = PdfConfig()
    vision: VisionConfig = VisionConfig()
    report: ReportConfig = ReportConfig()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Petra Vision"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    ENABLE_UI: bool = True

    OPENAI_API_KEY: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "OPEN_AI_API_KEY"),
    )
    ANTHROPIC_API_KEY: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "ANTHROPIC_AI_API_KEY", "ANTROPIC_AI_API_KEY"),
    )
    COHERE_API_KEY: str | None = None
    TEXT_PROVIDER: Literal["openai", "claude"] = "openai"
    VISION_PROVIDER: Literal["openai", "claude"] = "openai"
    OPENAI_TEXT_MODEL: str = "gpt-5.4-mini"
    OPENAI_VISION_MODEL: str | None = None
    OPENAI_TEXT_TEMPERATURE: float | None = None
    OPENAI_TEXT_MAX_COMPLETION_TOKENS: int | None = None
    CLAUDE_TEXT_MODEL: str = "claude-sonnet-4-6"
    CLAUDE_VISION_MODEL: str | None = None
    CLAUDE_TEXT_TEMPERATURE: float | None = None
    CLAUDE_VISION_TEMPERATURE: float | None = None
    CLAUDE_TEXT_MAX_TOKENS: int = 1600
    CLAUDE_VISION_MAX_TOKENS: int = 1600

    DATABASE_BACKEND: str = "sqlite"
    DATABASE_URL: str | None = None
    SQLITE_PATH: str = "data/petra.db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "petra"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    APP_ADMIN_EMAIL: str = "admin@example.com"
    APP_ADMIN_PASSWORD: str = "admin"

    STORAGE_BACKEND: str = "local"
    PUBLIC_DIR: str = "public"
    LOCAL_WORKDIR: str = "data/tmp"

    S3_BUCKET: str | None = None
    S3_REGION: str | None = None
    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None

    AZURE_BLOB_CONNECTION_STRING: str | None = None
    AZURE_BLOB_CONTAINER: str | None = None

    @field_validator("TEXT_PROVIDER", "VISION_PROVIDER", mode="before")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        normalized = str(value or "openai").strip().lower().replace("_", " ").replace("-", " ")
        provider_aliases = {
            "openai": "openai",
            "open ai": "openai",
            "claude": "claude",
            "anthropic": "claude",
        }
        if normalized not in provider_aliases:
            raise ValueError(f"Unsupported provider '{value}'. Expected one of: openai, claude.")
        return provider_aliases[normalized]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def build_database_url(settings: Settings) -> str:
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    if settings.DATABASE_BACKEND == "postgresql":
        return (
            f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
    return f"sqlite:///{settings.SQLITE_PATH}"


@lru_cache(maxsize=1)
def load_app_yaml(path: str = "config/app.yaml") -> AppYaml:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return AppYaml(**data)


def project_paths(app: AppYaml) -> dict[str, Path]:
    root = Path(".").resolve()
    return {
        "uploads": root / app.paths.uploads_dir,
        "indexes": root / app.paths.indexes_dir,
        "reports": root / app.paths.reports_dir,
    }
