from __future__ import annotations

import time
from pathlib import Path

from src.core.config import AppYaml, Settings
from src.pipeline.pdf_extractor import PdfExtractor
from src.pipeline.text_rule_analyzer import TextRuleAnalyzer
from src.pipeline.result_builder import build_document_result


def _timestamp_id() -> str:
    return time.strftime("%Y%m%dT%H%M%S")


class ValidationPipeline:
    def __init__(self, app_config: AppYaml, settings: Settings) -> None:
        self.app_config = app_config
        self.settings = settings
        self.extractor = PdfExtractor(app_config=app_config)
        self.text_rule_analyzer = TextRuleAnalyzer(settings=settings)

    def run(
        self,
        pdf_path: str,
        rules: list[dict] | None = None,
        source_filename: str | None = None,
        source_pdf_url: str | None = None,
    ) -> dict:
        doc_id = Path(pdf_path).stem + f"_{_timestamp_id()}"
        pages = self.extractor.extract(pdf_path=pdf_path)
        selected_rules = rules or []
        text_analysis_results = self.text_rule_analyzer.analyze(pages=pages, rules=selected_rules)
        text_rule_results = text_analysis_results.get("rule_results", {})
        text_page_results = text_analysis_results.get("page_results", [])
        rule_assessments = []
        for rule in selected_rules:
            rule_id = rule.get("id", "")
            analysis_type = rule.get("analysis_type", "text")
            if analysis_type == "text":
                rule_assessments.append(
                    text_rule_results.get(
                        rule_id,
                        {
                            "rule_id": rule_id,
                            "rule_name": rule.get("name", rule_id),
                            "analysis_type": "text",
                            "execution_status": "skipped",
                            "verdict": "needs_review",
                            "summary": "No text analysis result was produced.",
                            "reasoning": "No text analysis result was produced.",
                            "findings": [],
                            "citations": [],
                            "matched_pages": [],
                            "notes": ["No text analysis result was produced."],
                        },
                    )
                )
                continue

            rule_assessments.append(
                {
                    "rule_id": rule_id,
                    "rule_name": rule.get("name", rule_id),
                    "analysis_type": "vision",
                    "execution_status": "pending",
                    "verdict": "needs_review",
                    "summary": "Vision analysis is prepared but not yet executed in this build.",
                    "reasoning": "The rule is marked as visual and will be evaluated when the image pipeline is enabled.",
                    "findings": [],
                    "citations": [],
                    "matched_pages": [],
                    "notes": ["Vision analysis pending integration."],
                }
            )
        return build_document_result(
            document_id=doc_id,
            pages=pages,
            source_filename=source_filename,
            source_pdf_url=source_pdf_url,
            selected_rules=selected_rules,
            rule_assessments=rule_assessments,
            text_page_results=text_page_results,
        )
