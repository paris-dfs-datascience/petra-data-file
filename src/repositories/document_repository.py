from __future__ import annotations

from sqlalchemy.orm import Session

from src.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        original_filename: str,
        storage_path: str,
        external_id: str | None = None,
        public_url: str | None = None,
        uploaded_by: int | None = None,
    ) -> Document:
        document = Document(
            external_id=external_id,
            original_filename=original_filename,
            storage_path=storage_path,
            public_url=public_url,
            uploaded_by=uploaded_by,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
