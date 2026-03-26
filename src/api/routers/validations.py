from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from src.core.config import get_settings
from src.providers.storage.factory import get_storage_provider
from src.schemas.validation import DocumentValidationResponse
from src.services.document_service import DocumentService
from src.services.validation_service import ValidationService


router = APIRouter(prefix="/validations", tags=["validations"])


@router.post("", response_model=DocumentValidationResponse)
async def validate_document(
    pdf: UploadFile = File(..., description="PDF file"),
    rules_json: str | None = Form(None, description="Selected rules JSON"),
) -> DocumentValidationResponse:
    settings = get_settings()
    document_service = DocumentService(storage=get_storage_provider(settings), workdir=settings.LOCAL_WORKDIR)
    upload = document_service.prepare_upload_for_processing(filename=pdf.filename or "document.pdf", content=await pdf.read())
    service = ValidationService()
    try:
        result = service.validate_document(
            pdf_path=upload.local_processing_path,
            source_filename=upload.filename,
            source_pdf_url=upload.public_url,
            rules_json_str=rules_json,
        )
        return DocumentValidationResponse(**result)
    finally:
        try:
            Path(upload.local_processing_path).unlink(missing_ok=True)
        except Exception:
            pass
