from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    started_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(100))
    model_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="completed")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ValidationPageResult(Base):
    __tablename__ = "validation_page_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    validation_run_id: Mapped[int] = mapped_column(ForeignKey("validation_runs.id"))
    page_number: Mapped[int] = mapped_column(Integer)
    image_path: Mapped[str] = mapped_column(String(1024))
    image_path_centerline: Mapped[str | None] = mapped_column(String(1024), nullable=True)


class ValidationRuleResult(Base):
    __tablename__ = "validation_rule_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    page_result_id: Mapped[int] = mapped_column(ForeignKey("validation_page_results.id"))
    rule_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))
    reasoning: Mapped[str] = mapped_column(Text)
    citations_json: Mapped[list] = mapped_column(JSON, default=list)
    preview_images_json: Mapped[list] = mapped_column(JSON, default=list)
