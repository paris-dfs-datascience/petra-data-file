from __future__ import annotations

import time
from pathlib import Path

from src.core.config import AppYaml, Settings
from src.pipeline.pdf_extractor import PdfExtractor
from src.pipeline.result_builder import build_document_result


def _timestamp_id() -> str:
    return time.strftime("%Y%m%dT%H%M%S")


class ValidationPipeline:
    def __init__(self, app_config: AppYaml, settings: Settings) -> None:
        self.app_config = app_config
        self.settings = settings
        self.extractor = PdfExtractor()

    def run(
        self,
        pdf_path: str,
        rules: list[dict] | None = None,
        source_filename: str | None = None,
        source_pdf_url: str | None = None,
    ) -> dict:
        doc_id = Path(pdf_path).stem + f"_{_timestamp_id()}"
        pages = self.extractor.extract(pdf_path=pdf_path)
        return build_document_result(
            document_id=doc_id,
            pages=pages,
            source_filename=source_filename,
            source_pdf_url=source_pdf_url,
            selected_rules=rules,
        )
