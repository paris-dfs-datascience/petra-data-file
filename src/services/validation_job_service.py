from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.database import SessionLocal
from src.pipeline.result_builder import build_document_result
from src.repositories.validation_repository import ValidationRepository
from src.services.validation_service import ValidationService


@dataclass
class ValidationJobSnapshot:
    job_id: str
    status: str
    message: str
    progress_current: int = 0
    progress_total: int = 0
    error: str | None = None
    result: dict[str, Any] | None = None


class ValidationJobService:
    def _build_provider_identity(self, service: ValidationService) -> dict[str, str]:
        settings = service.settings
        app_config = service.app_config

        text_model = settings.OPENAI_TEXT_MODEL if settings.TEXT_PROVIDER == "openai" else settings.CLAUDE_TEXT_MODEL
        if settings.VISION_PROVIDER == "openai":
            vision_model = settings.OPENAI_VISION_MODEL or app_config.vision.model_id
        else:
            vision_model = settings.CLAUDE_VISION_MODEL or settings.CLAUDE_TEXT_MODEL

        provider = settings.TEXT_PROVIDER if settings.TEXT_PROVIDER == settings.VISION_PROVIDER else "mixed"
        model_id = text_model if settings.TEXT_PROVIDER == settings.VISION_PROVIDER else f"{text_model} + {vision_model}"

        return {
            "provider": provider,
            "model_id": model_id,
            "text_provider": settings.TEXT_PROVIDER,
            "text_model_id": text_model,
            "vision_provider": settings.VISION_PROVIDER,
            "vision_model_id": vision_model,
        }

    def _snapshot_from_run(self, run) -> ValidationJobSnapshot:
        return ValidationJobSnapshot(
            job_id=run.job_id or "",
            status=run.status,
            message=run.message or "",
            progress_current=run.progress_current or 0,
            progress_total=run.progress_total or 0,
            error=run.error_message,
            result=run.result_json,
        )

    def start_job(
        self,
        pdf_path: str,
        source_filename: str | None,
        source_pdf_url: str | None,
        rules_json_str: str | None,
        document_id: int | None = None,
        selected_rules: list[dict] | None = None,
    ) -> ValidationJobSnapshot:
        service = ValidationService()
        resolved_rules = selected_rules if selected_rules is not None else service.rule_service.load_rules(rules_json_str=rules_json_str)
        identity = self._build_provider_identity(service)
        job_id = uuid.uuid4().hex

        with SessionLocal() as db:
            repo = ValidationRepository(db)
            run = repo.create_run(
                provider=identity["provider"],
                model_id=identity["model_id"],
                document_id=document_id,
                job_id=job_id,
                mode="async",
                status="queued",
                message="Queued",
                source_filename=source_filename,
                source_pdf_url=source_pdf_url,
                text_provider=identity["text_provider"],
                text_model_id=identity["text_model_id"],
                vision_provider=identity["vision_provider"],
                vision_model_id=identity["vision_model_id"],
                selected_rules_json=resolved_rules,
            )
            snapshot = self._snapshot_from_run(run)
            run_id = run.id

        thread = threading.Thread(
            target=self._run_job,
            args=(run_id, pdf_path, source_filename, source_pdf_url, resolved_rules),
            daemon=True,
        )
        thread.start()
        return snapshot

    def get_job(self, job_id: str) -> ValidationJobSnapshot | None:
        with SessionLocal() as db:
            run = ValidationRepository(db).get_by_job_id(job_id)
            if run is None:
                return None
            return self._snapshot_from_run(run)

    def cancel_job(self, job_id: str) -> ValidationJobSnapshot | None:
        with SessionLocal() as db:
            repo = ValidationRepository(db)
            run = repo.get_by_job_id(job_id)
            if run is None:
                return None

            message = run.message
            if run.status in {"queued", "running"}:
                message = "Stopping analysis"
            run = repo.update_run(run.id, cancel_requested=True, message=message)
            return self._snapshot_from_run(run)

    def _is_cancelled(self, run_id: int) -> bool:
        with SessionLocal() as db:
            run = ValidationRepository(db).get_by_id(run_id)
            return bool(run and run.cancel_requested)

    def _update_run(
        self,
        run_id: int,
        *,
        status: str | None = None,
        message: str | None = None,
        progress_current: int | None = None,
        progress_total: int | None = None,
        result_json: dict | None = None,
        page_count: int | None = None,
        error_message: str | None = None,
        finished_at: datetime | None = None,
    ) -> None:
        with SessionLocal() as db:
            ValidationRepository(db).update_run(
                run_id,
                status=status,
                message=message,
                progress_current=progress_current,
                progress_total=progress_total,
                result_json=result_json,
                page_count=page_count,
                error_message=error_message,
                finished_at=finished_at,
            )

    def _persist_run_details(self, run_id: int, result_json: dict) -> None:
        analysis = result_json.get("analysis", {})
        with SessionLocal() as db:
            ValidationRepository(db).replace_run_details(
                run_id,
                pages=result_json.get("pages", []),
                rule_assessments=analysis.get("rule_assessments", []),
                text_page_results=analysis.get("text_page_results", []),
                visual_page_results=analysis.get("visual_page_results", []),
            )

    def _run_job(
        self,
        run_id: int,
        pdf_path: str,
        source_filename: str | None,
        source_pdf_url: str | None,
        selected_rules: list[dict],
    ) -> None:
        service = ValidationService()
        text_rules = [rule for rule in selected_rules if rule.get("analysis_type", "text") == "text"]

        try:
            self._update_run(run_id, status="running", message="Extracting PDF", progress_total=max(1, len(text_rules)))

            pages = service.pipeline.extractor.extract(pdf_path=pdf_path)
            text_total_steps = len(text_rules) * max(1, len(pages))
            vision_total_steps = service.pipeline.vision_rule_analyzer.estimate_step_count(len(pages), selected_rules)
            total_steps = max(1, text_total_steps + vision_total_steps)

            initial_result = build_document_result(
                document_id=Path(pdf_path).stem,
                pages=pages,
                source_filename=source_filename,
                source_pdf_url=source_pdf_url,
                selected_rules=selected_rules,
                rule_assessments=service.pipeline.build_rule_assessments(
                    selected_rules=selected_rules,
                    text_rule_results={},
                    vision_rule_results={},
                    default_text_status="running",
                    default_vision_status="pending",
                ),
                text_page_results=[],
                visual_page_results=[],
            )
            self._update_run(
                run_id,
                progress_total=total_steps,
                result_json=initial_result,
                page_count=len(pages),
            )

            def on_text_page_result(page_result: dict, current_rule_results: dict[str, dict], current_page_results: list[dict]) -> None:
                current_page = page_result.get("page", 0)
                current_rule = page_result.get("rule_name", page_result.get("rule_id", ""))
                partial_result = build_document_result(
                    document_id=Path(pdf_path).stem,
                    pages=pages,
                    source_filename=source_filename,
                    source_pdf_url=source_pdf_url,
                    selected_rules=selected_rules,
                    rule_assessments=service.pipeline.build_rule_assessments(
                        selected_rules=selected_rules,
                        text_rule_results=current_rule_results,
                        vision_rule_results={},
                        default_text_status="running",
                        default_vision_status="pending",
                    ),
                    text_page_results=current_page_results,
                    visual_page_results=[],
                )
                self._update_run(
                    run_id,
                    message=f"Analyzing page {current_page} - {current_rule}",
                    progress_current=min(len(current_page_results), total_steps),
                    result_json=partial_result,
                    page_count=len(pages),
                )

            text_analysis_results = service.pipeline.text_rule_analyzer.analyze(
                pages=pages,
                rules=selected_rules,
                on_page_result=on_text_page_result,
                is_cancelled=lambda: self._is_cancelled(run_id),
            )

            text_rule_results = text_analysis_results.get("rule_results", {})
            text_page_results = text_analysis_results.get("page_results", [])

            if self._is_cancelled(run_id):
                final_result = build_document_result(
                    document_id=Path(pdf_path).stem,
                    pages=pages,
                    source_filename=source_filename,
                    source_pdf_url=source_pdf_url,
                    selected_rules=selected_rules,
                    rule_assessments=service.pipeline.build_rule_assessments(
                        selected_rules=selected_rules,
                        text_rule_results=text_rule_results,
                        vision_rule_results={},
                        default_text_status="completed",
                        default_vision_status="pending",
                    ),
                    text_page_results=text_page_results,
                    visual_page_results=[],
                )
                self._update_run(
                    run_id,
                    status="cancelled",
                    message="Analysis stopped",
                    progress_current=min(len(text_page_results), total_steps),
                    progress_total=total_steps,
                    result_json=final_result,
                    page_count=len(pages),
                    finished_at=datetime.utcnow(),
                )
                self._persist_run_details(run_id, final_result)
                return

            vision_progress_offset = len(text_page_results)
            if vision_total_steps == 0:
                final_result = build_document_result(
                    document_id=Path(pdf_path).stem,
                    pages=pages,
                    source_filename=source_filename,
                    source_pdf_url=source_pdf_url,
                    selected_rules=selected_rules,
                    rule_assessments=service.pipeline.build_rule_assessments(
                        selected_rules=selected_rules,
                        text_rule_results=text_rule_results,
                        vision_rule_results={},
                        default_text_status="completed",
                        default_vision_status="skipped",
                    ),
                    text_page_results=text_page_results,
                    visual_page_results=[],
                )
                self._update_run(
                    run_id,
                    status="completed",
                    message="Analysis complete",
                    progress_current=total_steps,
                    progress_total=total_steps,
                    result_json=final_result,
                    page_count=len(pages),
                    finished_at=datetime.utcnow(),
                )
                self._persist_run_details(run_id, final_result)
                return

            rendering_result = build_document_result(
                document_id=Path(pdf_path).stem,
                pages=pages,
                source_filename=source_filename,
                source_pdf_url=source_pdf_url,
                selected_rules=selected_rules,
                rule_assessments=service.pipeline.build_rule_assessments(
                    selected_rules=selected_rules,
                    text_rule_results=text_rule_results,
                    vision_rule_results={},
                    default_text_status="completed",
                    default_vision_status="running",
                ),
                text_page_results=text_page_results,
                visual_page_results=[],
            )
            self._update_run(
                run_id,
                message="Rendering pages for visual analysis",
                progress_current=min(vision_progress_offset, total_steps),
                result_json=rendering_result,
                page_count=len(pages),
            )

            def on_vision_page_result(page_result: dict, current_rule_results: dict[str, dict], current_page_results: list[dict]) -> None:
                current_page = page_result.get("page", 0)
                current_rule = page_result.get("rule_name", page_result.get("rule_id", ""))
                partial_result = build_document_result(
                    document_id=Path(pdf_path).stem,
                    pages=pages,
                    source_filename=source_filename,
                    source_pdf_url=source_pdf_url,
                    selected_rules=selected_rules,
                    rule_assessments=service.pipeline.build_rule_assessments(
                        selected_rules=selected_rules,
                        text_rule_results=text_rule_results,
                        vision_rule_results=current_rule_results,
                        default_text_status="completed",
                        default_vision_status="running",
                    ),
                    text_page_results=text_page_results,
                    visual_page_results=current_page_results,
                )
                self._update_run(
                    run_id,
                    message=f"Analyzing visual page {current_page} - {current_rule}",
                    progress_current=min(vision_progress_offset + len(current_page_results), total_steps),
                    result_json=partial_result,
                    page_count=len(pages),
                )

            vision_analysis_results = service.pipeline.vision_rule_analyzer.analyze(
                pdf_path=pdf_path,
                rules=selected_rules,
                on_page_result=on_vision_page_result,
                is_cancelled=lambda: self._is_cancelled(run_id),
            )

            vision_rule_results = vision_analysis_results.get("rule_results", {})
            visual_page_results = vision_analysis_results.get("page_results", [])
            final_status = "cancelled" if self._is_cancelled(run_id) else "completed"
            final_message = "Analysis stopped" if final_status == "cancelled" else "Analysis complete"
            final_result = build_document_result(
                document_id=Path(pdf_path).stem,
                pages=pages,
                source_filename=source_filename,
                source_pdf_url=source_pdf_url,
                selected_rules=selected_rules,
                rule_assessments=service.pipeline.build_rule_assessments(
                    selected_rules=selected_rules,
                    text_rule_results=text_rule_results,
                    vision_rule_results=vision_rule_results,
                ),
                text_page_results=text_page_results,
                visual_page_results=visual_page_results,
            )
            self._update_run(
                run_id,
                status=final_status,
                message=final_message,
                progress_current=total_steps,
                progress_total=total_steps,
                result_json=final_result,
                page_count=len(pages),
                finished_at=datetime.utcnow(),
            )
            self._persist_run_details(run_id, final_result)
        except Exception as exc:
            self._update_run(
                run_id,
                status="failed",
                message="Analysis failed",
                error_message=str(exc),
                finished_at=datetime.utcnow(),
            )
        finally:
            try:
                Path(pdf_path).unlink(missing_ok=True)
            except Exception:
                pass


validation_job_service = ValidationJobService()
