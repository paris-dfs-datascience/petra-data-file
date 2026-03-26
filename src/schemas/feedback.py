from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class FeedbackItemSchema(BaseModel):
    rule_id: str
    page: int
    verdict: str
    note: Optional[str] = ""


class FeedbackRequestSchema(BaseModel):
    document_id: str
    items: list[FeedbackItemSchema]


class FeedbackResponse(BaseModel):
    status: str
    message: str
