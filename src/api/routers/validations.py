from __future__ import annotations

from pathlib import Path
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.core.config import get_settings
from src.schemas.validation import DocumentValidationResponse, ValidationJobResponse
from src.services.validation_service import ValidationService
from src.services.validation_job_service import validation_job_service


router = APIRouter(prefix="/validations", tags=["validations"])

PDF_MAGIC = b"%PDF-"


async def _read_and_validate_upload(pdf: UploadFile, max_size_mb: int) -> bytes:
    content = await pdf.read()
    if len(content) > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {max_size_mb} MB limit.")
    if pdf.content_type and pdf.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Only PDF files are accepted.")
    if not content.startswith(PDF_MAGIC):
        raise HTTPException(status_code=422, detail="File does not appear to be a valid PDF.")
    return content


def _stage_pdf_for_processing(filename: str, content: bytes, workdir: str) -> tuple[str, str]:
    safe_filename = Path(filename or "document.pdf").name or "document.pdf"
    temp_dir = Path(workdir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="upload_", suffix=".pdf", dir=str(temp_dir), delete=False) as handle:
        handle.write(content)
        return safe_filename, handle.name


@router.post("", response_model=DocumentValidationResponse)
async def validate_document(
    pdf: UploadFile = File(..., description="PDF file"),
    rules_json: str | None = Form(None, description="Selected rules JSON"),
) -> DocumentValidationResponse:
    settings = get_settings()
    content = await _read_and_validate_upload(pdf, settings.MAX_UPLOAD_SIZE_MB)
    filename, pdf_path = _stage_pdf_for_processing(
        filename=pdf.filename or "document.pdf",
        content=content,
        workdir=settings.LOCAL_WORKDIR,
    )
    service = ValidationService()
    try:
        result = service.validate_document(
            pdf_path=pdf_path,
            source_filename=filename,
            rules_json_str=rules_json,
        )
        return DocumentValidationResponse(**result)
    finally:
        try:
            Path(pdf_path).unlink(missing_ok=True)
        except Exception:
            pass


@router.post("/jobs", response_model=ValidationJobResponse)
async def create_validation_job(
    pdf: UploadFile = File(..., description="PDF file"),
    rules_json: str | None = Form(None, description="Selected rules JSON"),
) -> ValidationJobResponse:
    settings = get_settings()
    content = await _read_and_validate_upload(pdf, settings.MAX_UPLOAD_SIZE_MB)
    filename, pdf_path = _stage_pdf_for_processing(
        filename=pdf.filename or "document.pdf",
        content=content,
        workdir=settings.LOCAL_WORKDIR,
    )
    job = validation_job_service.start_job(
        pdf_path=pdf_path,
        source_filename=filename,
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
