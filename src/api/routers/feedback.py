from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from src.schemas.feedback import FeedbackCreate, FeedbackRecord, FeedbackResponse

router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])

FEEDBACK_FILE = Path("/app/data/feedback.json")


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(payload: FeedbackCreate) -> FeedbackResponse:
    record = FeedbackRecord(**payload.model_dump())
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    if FEEDBACK_FILE.exists():
        try:
            existing = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            existing = []

    existing.append(record.model_dump())
    FEEDBACK_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")

    return FeedbackResponse()
