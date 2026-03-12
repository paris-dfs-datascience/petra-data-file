from __future__ import annotations

import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import BaseModel
import yaml


class Paths(BaseModel):
    uploads_dir: str = "data/uploads"
    indexes_dir: str = "data/indexes"
    reports_dir: str = "data/reports"


class PDFConfig(BaseModel):
    dpi: int = 200
    image_format: Literal["png", "jpeg"] = "png"


class EmbeddingConfig(BaseModel):
    # Relaxed validation for unused config
    provider: str = "none"
    model_id: str = ""
    output_dimension: int = 1024
    embedding_type: str = "float"
    batch_size: int = 32
    use_inputs_object: bool = False


class RetrievalConfig(BaseModel):
    top_k: int = 5
    metric: str = "cosine"


class VisionConfig(BaseModel):
    provider: Literal["cohere", "openai"] = "cohere"
    model_id: str = "command-a-vision-07-2025"
    max_images_per_request: int = 10
    temperature: float = 0.1
    seed: int = 42
    max_completion_tokens: int = 1200
    image_detail: Literal["low", "high", "auto"] = "high"
    concurrent_requests: int = 4
    global_max_concurrent: int = 10


class ReportConfig(BaseModel):
    include_thumbnails: bool = False


class AppYaml(BaseModel):
    app: dict
    paths: Paths = Paths()
    pdf: PDFConfig = PDFConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    vision: VisionConfig = VisionConfig()
    report: ReportConfig = ReportConfig()


class Settings(BaseSettings):
    COHERE_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    VISION_PROVIDER: str = "cohere"
    EMBEDDING_PROVIDER: str = "cohere"

    class Config:
        env_file = ".env"
        extra = "ignore"


def load_app_yaml(path: str = "config/app.yaml") -> AppYaml:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return AppYaml(**data)


def project_paths(app: AppYaml) -> dict[str, Path]:
    root = Path(".").resolve()
    return {
        "uploads": (root / app.paths.uploads_dir),
        "indexes": (root / app.paths.indexes_dir),
        "reports": (root / app.paths.reports_dir),
    }
