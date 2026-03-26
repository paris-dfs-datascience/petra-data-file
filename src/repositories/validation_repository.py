from __future__ import annotations

from sqlalchemy.orm import Session

from src.models.validation import ValidationRun


class ValidationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_run(self, provider: str, model_id: str, document_id: int | None = None) -> ValidationRun:
        run = ValidationRun(provider=provider, model_id=model_id, document_id=document_id)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
