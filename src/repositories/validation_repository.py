from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.models.validation import ValidationPageResult, ValidationRuleAssessment, ValidationRuleResult, ValidationRun


class ValidationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_run(
        self,
        provider: str,
        model_id: str,
        document_id: int | None = None,
        job_id: str | None = None,
        mode: str = "sync",
        status: str = "queued",
        message: str | None = None,
        source_filename: str | None = None,
        source_pdf_url: str | None = None,
        text_provider: str | None = None,
        text_model_id: str | None = None,
        vision_provider: str | None = None,
        vision_model_id: str | None = None,
        selected_rules_json: list[dict] | None = None,
    ) -> ValidationRun:
        run = ValidationRun(
            provider=provider,
            model_id=model_id,
            document_id=document_id,
            job_id=job_id,
            mode=mode,
            status=status,
            message=message,
            source_filename=source_filename,
            source_pdf_url=source_pdf_url,
            text_provider=text_provider,
            text_model_id=text_model_id,
            vision_provider=vision_provider,
            vision_model_id=vision_model_id,
            selected_rules_json=selected_rules_json,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_by_id(self, run_id: int) -> ValidationRun | None:
        return self.db.get(ValidationRun, run_id)

    def get_by_job_id(self, job_id: str) -> ValidationRun | None:
        return self.db.scalar(select(ValidationRun).where(ValidationRun.job_id == job_id))

    def update_run(
        self,
        run_id: int,
        *,
        status: str | None = None,
        message: str | None = None,
        progress_current: int | None = None,
        progress_total: int | None = None,
        cancel_requested: bool | None = None,
        result_json: dict | None = None,
        page_count: int | None = None,
        error_message: str | None = None,
        finished_at: datetime | None = None,
    ) -> ValidationRun:
        run = self.get_by_id(run_id)
        if run is None:
            raise ValueError(f"Validation run {run_id} was not found.")

        if status is not None:
            run.status = status
        if message is not None:
            run.message = message
        if progress_current is not None:
            run.progress_current = progress_current
        if progress_total is not None:
            run.progress_total = progress_total
        if cancel_requested is not None:
            run.cancel_requested = cancel_requested
        if result_json is not None:
            run.result_json = result_json
        if page_count is not None:
            run.page_count = page_count
        if error_message is not None:
            run.error_message = error_message
        if finished_at is not None:
            run.finished_at = finished_at

        self.db.commit()
        self.db.refresh(run)
        return run

    def replace_run_details(
        self,
        run_id: int,
        *,
        pages: list[dict],
        rule_assessments: list[dict],
        text_page_results: list[dict],
        visual_page_results: list[dict],
    ) -> None:
        self.db.execute(delete(ValidationRuleAssessment).where(ValidationRuleAssessment.validation_run_id == run_id))

        existing_page_result_ids = list(
            self.db.scalars(
                select(ValidationPageResult.id).where(ValidationPageResult.validation_run_id == run_id)
            ).all()
        )
        if existing_page_result_ids:
            self.db.execute(
                delete(ValidationRuleResult).where(ValidationRuleResult.page_result_id.in_(existing_page_result_ids))
            )

        self.db.execute(delete(ValidationPageResult).where(ValidationPageResult.validation_run_id == run_id))
        self.db.flush()

        for item in rule_assessments:
            self.db.add(
                ValidationRuleAssessment(
                    validation_run_id=run_id,
                    rule_id=item.get("rule_id", ""),
                    rule_name=item.get("rule_name"),
                    analysis_type=item.get("analysis_type"),
                    execution_status=item.get("execution_status"),
                    verdict=item.get("verdict"),
                    summary=item.get("summary"),
                    reasoning=item.get("reasoning"),
                    citations_json=item.get("citations", []),
                    findings_json=item.get("findings", []),
                    notes_json=item.get("notes", []),
                    matched_pages_json=item.get("matched_pages", []),
                    raw_result_json=item,
                )
            )

        page_result_map: dict[int, ValidationPageResult] = {}
        for page in pages:
            page_number = int(page.get("page", 0) or 0)
            page_result = ValidationPageResult(
                validation_run_id=run_id,
                page_number=page_number,
                image_path="",
                image_path_centerline=None,
                extracted_text=page.get("text", ""),
                char_count=int(page.get("char_count", 0) or 0),
                tables_json=page.get("tables", []),
                layout_summary_json=page.get("layout_summary"),
                page_payload_json=page,
            )
            self.db.add(page_result)
            self.db.flush()
            page_result_map[page_number] = page_result

        for item in [*text_page_results, *visual_page_results]:
            page_number = int(item.get("page", 0) or 0)
            page_result = page_result_map.get(page_number)
            if page_result is None:
                continue

            self.db.add(
                ValidationRuleResult(
                    page_result_id=page_result.id,
                    page_number=page_number,
                    rule_id=item.get("rule_id", ""),
                    rule_name=item.get("rule_name"),
                    analysis_type=item.get("analysis_type"),
                    status=item.get("execution_status", "completed"),
                    verdict=item.get("verdict"),
                    summary=item.get("summary", ""),
                    reasoning=item.get("reasoning", ""),
                    citations_json=item.get("citations", []),
                    findings_json=item.get("findings", []),
                    notes_json=item.get("notes", []),
                    raw_result_json=item,
                    preview_images_json=[],
                )
            )

        self.db.commit()
