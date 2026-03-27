from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.core.config import get_settings
from src.providers.storage.factory import get_storage_provider
from src.schemas.validation import DocumentValidationResponse, ValidationJobResponse
from src.services.document_service import DocumentService
from src.services.validation_service import ValidationService
from src.services.validation_job_service import validation_job_service


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


@router.post("/jobs", response_model=ValidationJobResponse)
async def create_validation_job(
    pdf: UploadFile = File(..., description="PDF file"),
    rules_json: str | None = Form(None, description="Selected rules JSON"),
) -> ValidationJobResponse:
    settings = get_settings()
    document_service = DocumentService(storage=get_storage_provider(settings), workdir=settings.LOCAL_WORKDIR)
    upload = document_service.prepare_upload_for_processing(filename=pdf.filename or "document.pdf", content=await pdf.read())
    job = validation_job_service.start_job(
        pdf_path=upload.local_processing_path,
        source_filename=upload.filename,
        source_pdf_url=upload.public_url,
        rules_json_str=rules_json,
    )
    return ValidationJobResponse(
        job_id=job.job_id,
        status=job.status,
        message=job.message,
        progress_current=job.progress_current,
        progress_total=job.progress_total,
    )


@router.get("/jobs/{job_id}", response_model=ValidationJobResponse)
async def get_validation_job(job_id: str) -> ValidationJobResponse:
    job = validation_job_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Validation job not found.")
    with job.lock:
        result = DocumentValidationResponse(**job.result) if job.result else None
        return ValidationJobResponse(
            job_id=job.job_id,
            status=job.status,
            message=job.message,
            progress_current=job.progress_current,
            progress_total=job.progress_total,
            error=job.error,
            result=result,
        )


@router.post("/jobs/{job_id}/cancel", response_model=ValidationJobResponse)
async def cancel_validation_job(job_id: str) -> ValidationJobResponse:
    job = validation_job_service.cancel_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Validation job not found.")
    with job.lock:
        result = DocumentValidationResponse(**job.result) if job.result else None
        return ValidationJobResponse(
            job_id=job.job_id,
            status=job.status,
            message=job.message,
            progress_current=job.progress_current,
            progress_total=job.progress_total,
            error=job.error,
            result=result,
        )
