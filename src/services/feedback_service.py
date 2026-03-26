from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.schemas.feedback import FeedbackRequestSchema, FeedbackResponse


class FeedbackService:
    def append_feedback(self, data: FeedbackRequestSchema) -> FeedbackResponse:
        feedback_dir = Path("data/feedback")
        feedback_dir.mkdir(parents=True, exist_ok=True)
        feedback_file = feedback_dir / "feedback.jsonl"
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "document_id": data.document_id,
            "items": [item.model_dump() for item in data.items],
        }
        with open(feedback_file, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
        return FeedbackResponse(status="ok", message=f"Logged {len(data.items)} feedback item(s).")
