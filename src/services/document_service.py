from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from src.providers.storage.base import StorageProvider
from src.schemas.document import DocumentUploadResponse


@dataclass
class StoredUpload:
    document_id: str
    filename: str
    storage_path: str
    local_processing_path: str
    public_url: str | None = None


class DocumentService:
    def __init__(self, storage: StorageProvider, workdir: str) -> None:
        self.storage = storage
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)

    def _build_names(self, filename: str) -> tuple[str, str, str]:
        original_name = Path(filename or "document").stem
        safe_name = re.sub(r"[^a-zA-Z0-9_\\-]", "_", original_name)
        unique_suffix = uuid.uuid4().hex[:8]
        return safe_name, unique_suffix, f"{safe_name}_{unique_suffix}"

    def save_upload(self, filename: str, content: bytes) -> DocumentUploadResponse:
        safe_name, unique_suffix, document_id = self._build_names(filename)
        relative_path = f"uploads/originals/{safe_name}_{unique_suffix}.pdf"
        storage_path = self.storage.save_bytes(relative_path, content, content_type="application/pdf")
        return DocumentUploadResponse(
            document_id=document_id,
            filename=f"{safe_name}.pdf",
            storage_path=storage_path,
            public_url=self.storage.get_public_url(relative_path),
        )

    def prepare_upload_for_processing(self, filename: str, content: bytes) -> StoredUpload:
        safe_name, unique_suffix, document_id = self._build_names(filename)
        relative_path = f"uploads/originals/{safe_name}_{unique_suffix}.pdf"
        storage_path = self.storage.save_bytes(relative_path, content, content_type="application/pdf")
        local_path = self.workdir / f"{document_id}.pdf"
        local_path.write_bytes(content)
        return StoredUpload(
            document_id=document_id,
            filename=f"{safe_name}.pdf",
            storage_path=storage_path,
            local_processing_path=str(local_path),
            public_url=self.storage.get_public_url(relative_path),
        )
