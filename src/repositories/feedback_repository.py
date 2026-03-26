from __future__ import annotations

from sqlalchemy.orm import Session

from src.models.feedback import Feedback


class FeedbackRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, page_number: int, rule_id: str, verdict: str, note: str | None = None) -> Feedback:
        item = Feedback(page_number=page_number, rule_id=rule_id, verdict=verdict, note=note)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
