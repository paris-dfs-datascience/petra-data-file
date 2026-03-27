from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.pipeline.result_builder import build_document_result
from src.services.validation_service import ValidationService


@dataclass
class ValidationJob:
    job_id: str
    status: str = "queued"
    message: str = "Queued"
    progress_current: int = 0
    progress_total: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    cancel_requested: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)


class ValidationJobService:
    def __init__(self) -> None:
        self._jobs: dict[str, ValidationJob] = {}
        self._jobs_lock = threading.Lock()

    def start_job(
        self,
        pdf_path: str,
        source_filename: str | None,
        source_pdf_url: str | None,
        rules_json_str: str | None,
    ) -> ValidationJob:
        job = ValidationJob(job_id=uuid.uuid4().hex)
        with self._jobs_lock:
            self._jobs[job.job_id] = job
        thread = threading.Thread(
            target=self._run_job,
            args=(job.job_id, pdf_path, source_filename, source_pdf_url, rules_json_str),
            daemon=True,
        )
        thread.start()
        return job

    def get_job(self, job_id: str) -> ValidationJob | None:
        with self._jobs_lock:
            return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> ValidationJob | None:
        job = self.get_job(job_id)
        if job is None:
            return None
        with job.lock:
            job.cancel_requested = True
            if job.status in {"queued", "running"}:
                job.message = "Stopping analysis"
        return job

    def _build_rule_assessments(self, selected_rules: list[dict], text_rule_results: dict[str, dict]) -> list[dict]:
        rule_assessments: list[dict] = []
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
                            "execution_status": "running",
                            "verdict": "needs_review",
                            "summary": "Waiting for page-level text analysis results.",
                            "reasoning": "",
                            "findings": [],
                            "citations": [],
                            "matched_pages": [],
                            "notes": [],
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
        return rule_assessments

    def _run_job(
        self,
        job_id: str,
        pdf_path: str,
        source_filename: str | None,
        source_pdf_url: str | None,
        rules_json_str: str | None,
    ) -> None:
        job = self.get_job(job_id)
        if job is None:
            return

        service = ValidationService()
        selected_rules = service.rule_service.load_rules(rules_json_str=rules_json_str)
        text_rules = [rule for rule in selected_rules if rule.get("analysis_type", "text") == "text"]
        total_steps = max(1, len(text_rules))

        try:
            with job.lock:
                job.status = "running"
                job.message = "Extracting PDF"
                job.progress_total = total_steps

            pages = service.pipeline.extractor.extract(pdf_path=pdf_path)
            total_steps = max(1, len(text_rules) * max(1, len(pages)))
            with job.lock:
                job.progress_total = total_steps
            with job.lock:
                job.result = build_document_result(
                    document_id=Path(pdf_path).stem,
                    pages=pages,
                    source_filename=source_filename,
                    source_pdf_url=source_pdf_url,
                    selected_rules=selected_rules,
                    rule_assessments=self._build_rule_assessments(selected_rules, {}),
                    text_page_results=[],
                )

            def on_page_result(page_result: dict, current_rule_results: dict[str, dict], current_page_results: list[dict]) -> None:
                current_page = page_result.get("page", 0)
                current_rule = page_result.get("rule_name", page_result.get("rule_id", ""))
                with job.lock:
                    completed_pages = len(current_page_results)
                    job.message = f"Analyzing page {current_page} - {current_rule}"
                    job.progress_current = min(completed_pages, job.progress_total)
                    job.result = build_document_result(
                        document_id=Path(pdf_path).stem,
                        pages=pages,
                        source_filename=source_filename,
                        source_pdf_url=source_pdf_url,
                        selected_rules=selected_rules,
                        rule_assessments=self._build_rule_assessments(selected_rules, current_rule_results),
                        text_page_results=current_page_results,
                    )

            text_analysis_results = service.pipeline.text_rule_analyzer.analyze(
                pages=pages,
                rules=selected_rules,
                on_page_result=on_page_result,
                is_cancelled=lambda: bool(job.cancel_requested),
            )

            text_rule_results = text_analysis_results.get("rule_results", {})
            text_page_results = text_analysis_results.get("page_results", [])
            final_status = "cancelled" if job.cancel_requested else "completed"
            final_message = "Analysis stopped" if job.cancel_requested else "Analysis complete"

            with job.lock:
                job.status = final_status
                job.message = final_message
                job.progress_current = job.progress_total
                job.result = build_document_result(
                    document_id=Path(pdf_path).stem,
                    pages=pages,
                    source_filename=source_filename,
                    source_pdf_url=source_pdf_url,
                    selected_rules=selected_rules,
                    rule_assessments=self._build_rule_assessments(selected_rules, text_rule_results),
                    text_page_results=text_page_results,
                )
        except Exception as exc:
            with job.lock:
                job.status = "failed"
                job.message = "Analysis failed"
                job.error = str(exc)
        finally:
            try:
                Path(pdf_path).unlink(missing_ok=True)
            except Exception:
                pass


validation_job_service = ValidationJobService()
