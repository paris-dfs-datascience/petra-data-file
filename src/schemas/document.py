from __future__ import annotations

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    storage_path: str
    public_url: str | None = None
