from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    document_id: str
    source_filename: Optional[str] = None
    page: Optional[int] = None
    rule_id: str
    rule_name: str
    analysis_type: Literal["text", "vision"]
    verdict: str
    summary: str
    reasoning: str
    assessment: Literal["correct", "incorrect"]
    comment: Optional[str] = None


class FeedbackRecord(FeedbackCreate):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FeedbackResponse(BaseModel):
    status: str = "ok"
