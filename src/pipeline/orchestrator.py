from __future__ import annotations

import time
from pathlib import Path

from src.core.config import AppYaml, Settings, project_paths
from src.pipeline.pdf_renderer import PdfRenderer
from src.pipeline.result_builder import build_document_result
from src.pipeline.rule_evaluator import RuleEvaluator
from src.providers.vision.openai import OpenAIVisionProvider


def _timestamp_id() -> str:
    return time.strftime("%Y%m%dT%H%M%S")


class ValidationPipeline:
    def __init__(self, app_config: AppYaml, settings: Settings) -> None:
        self.app_config = app_config
        self.settings = settings
        self.renderer = PdfRenderer()

    def run(self, pdf_path: str, rules: list[dict]) -> dict:
        paths = project_paths(self.app_config)
        doc_id = Path(pdf_path).stem + f"_{_timestamp_id()}"
        out_dir = paths["uploads"] / doc_id / "pages"
        image_paths = self.renderer.render(
            pdf_path=pdf_path,
            out_dir=str(out_dir),
            dpi=self.app_config.pdf.dpi,
            image_format=self.app_config.pdf.image_format,
        )

        provider = OpenAIVisionProvider(
            api_key=self.settings.OPENAI_API_KEY or "",
            model_id=self.app_config.vision.model_id,
            temperature=self.app_config.vision.temperature,
            seed=self.app_config.vision.seed,
            max_completion_tokens=self.app_config.vision.max_completion_tokens,
            image_detail=self.app_config.vision.image_detail,
            max_concurrent=self.app_config.vision.global_max_concurrent,
        )
        evaluator = RuleEvaluator(provider=provider, concurrent_requests=self.app_config.vision.concurrent_requests)
        pages = evaluator.evaluate_pages(image_paths=image_paths, rules=rules, system_prompt_path="config/system_prompt.md")
        return build_document_result(document_id=doc_id, pages=pages)
