from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    started_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(100))
    model_id: Mapped[str] = mapped_column(String(255))
    job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mode: Mapped[str] = mapped_column(String(50), default="sync")
    status: Mapped[str] = mapped_column(String(50), default="completed")
    message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_pdf_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    text_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    text_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vision_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vision_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    selected_rules_json: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ValidationPageResult(Base):
    __tablename__ = "validation_page_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    validation_run_id: Mapped[int] = mapped_column(ForeignKey("validation_runs.id"))
    page_number: Mapped[int] = mapped_column(Integer)
    image_path: Mapped[str] = mapped_column(String(1024), default="")
    image_path_centerline: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    tables_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    layout_summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    page_payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ValidationRuleAssessment(Base):
    __tablename__ = "validation_rule_assessments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    validation_run_id: Mapped[int] = mapped_column(ForeignKey("validation_runs.id"))
    rule_id: Mapped[str] = mapped_column(String(255))
    rule_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    analysis_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    execution_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    verdict: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    citations_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    findings_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    notes_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    matched_pages_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    raw_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ValidationRuleResult(Base):
    __tablename__ = "validation_rule_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    page_result_id: Mapped[int] = mapped_column(ForeignKey("validation_page_results.id"))
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rule_id: Mapped[str] = mapped_column(String(255))
    rule_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    analysis_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50))
    verdict: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reasoning: Mapped[str] = mapped_column(Text)
    citations_json: Mapped[list] = mapped_column(JSON, default=list)
    findings_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    notes_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    raw_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    preview_images_json: Mapped[list] = mapped_column(JSON, default=list)
