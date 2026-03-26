from __future__ import annotations

from sqlalchemy.orm import Session

from src.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, original_filename: str, storage_path: str, uploaded_by: int | None = None) -> Document:
        document = Document(original_filename=original_filename, storage_path=storage_path, uploaded_by=uploaded_by)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
