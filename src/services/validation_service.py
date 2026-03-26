from __future__ import annotations

from src.core.config import get_settings, load_app_yaml
from src.pipeline.orchestrator import ValidationPipeline
from src.services.rule_service import RuleService


class ValidationService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.app_config = load_app_yaml()
        self.rule_service = RuleService()
        self.pipeline = ValidationPipeline(app_config=self.app_config, settings=self.settings)

    def validate_document(
        self,
        pdf_path: str,
        source_filename: str | None = None,
        source_pdf_url: str | None = None,
        rules_json_path: str | None = None,
        rules_json_str: str | None = None,
    ) -> dict:
        selected_rules = self.rule_service.load_rules(rules_json_path=rules_json_path, rules_json_str=rules_json_str)
        return self.pipeline.run(
            pdf_path=pdf_path,
            source_filename=source_filename,
            source_pdf_url=source_pdf_url,
            rules=selected_rules,
        )
