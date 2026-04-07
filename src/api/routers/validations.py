from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import get_db
from src.providers.storage.factory import get_storage_provider
from src.repositories.document_repository import DocumentRepository
from src.repositories.validation_repository import ValidationRepository
from src.schemas.validation import DocumentValidationResponse, ValidationJobResponse
from src.services.document_service import DocumentService
from src.services.validation_service import ValidationService
from src.services.validation_job_service import validation_job_service


router = APIRouter(prefix="/validations", tags=["validations"])


def _build_provider_identity(service: ValidationService) -> dict[str, str]:
    settings = service.settings
    app_config = service.app_config

    text_model = settings.OPENAI_TEXT_MODEL if settings.TEXT_PROVIDER == "openai" else settings.CLAUDE_TEXT_MODEL
    if settings.VISION_PROVIDER == "openai":
        vision_model = settings.OPENAI_VISION_MODEL or app_config.vision.model_id
    else:
        vision_model = settings.CLAUDE_VISION_MODEL or settings.CLAUDE_TEXT_MODEL

    provider = settings.TEXT_PROVIDER if settings.TEXT_PROVIDER == settings.VISION_PROVIDER else "mixed"
    model_id = text_model if settings.TEXT_PROVIDER == settings.VISION_PROVIDER else f"{text_model} + {vision_model}"

    return {
        "provider": provider,
        "model_id": model_id,
        "text_provider": settings.TEXT_PROVIDER,
        "text_model_id": text_model,
        "vision_provider": settings.VISION_PROVIDER,
        "vision_model_id": vision_model,
    }


@router.post("", response_model=DocumentValidationResponse)
async def validate_document(
    pdf: UploadFile = File(..., description="PDF file"),
    rules_json: str | None = Form(None, description="Selected rules JSON"),
    db: Session = Depends(get_db),
) -> DocumentValidationResponse:
    settings = get_settings()
    document_service = DocumentService(storage=get_storage_provider(settings), workdir=settings.LOCAL_WORKDIR)
    upload = document_service.prepare_upload_for_processing(filename=pdf.filename or "document.pdf", content=await pdf.read())
    service = ValidationService()
    selected_rules = service.rule_service.load_rules(rules_json_str=rules_json)
    document = DocumentRepository(db).create(
        external_id=upload.document_id,
        original_filename=upload.filename,
        storage_path=upload.storage_path,
        public_url=upload.public_url,
    )
    identity = _build_provider_identity(service)
    run = ValidationRepository(db).create_run(
        provider=identity["provider"],
        model_id=identity["model_id"],
        document_id=document.id,
        mode="sync",
        status="running",
        message="Processing validation request",
        source_filename=upload.filename,
        source_pdf_url=upload.public_url,
        text_provider=identity["text_provider"],
        text_model_id=identity["text_model_id"],
        vision_provider=identity["vision_provider"],
        vision_model_id=identity["vision_model_id"],
        selected_rules_json=selected_rules,
    )
    try:
        result = service.validate_document(
            pdf_path=upload.local_processing_path,
            source_filename=upload.filename,
            source_pdf_url=upload.public_url,
            rules=selected_rules,
        )
        repo = ValidationRepository(db)
        repo.update_run(
            run.id,
            status="completed",
            message="Analysis complete",
            progress_current=1,
            progress_total=1,
            result_json=result,
            page_count=result.get("page_count", 0),
            finished_at=datetime.utcnow(),
        )
        repo.replace_run_details(
            run.id,
            pages=result.get("pages", []),
            rule_assessments=result.get("analysis", {}).get("rule_assessments", []),
            text_page_results=result.get("analysis", {}).get("text_page_results", []),
            visual_page_results=result.get("analysis", {}).get("visual_page_results", []),
        )
        return DocumentValidationResponse(**result)
    except Exception as exc:
        ValidationRepository(db).update_run(
            run.id,
            status="failed",
            message="Analysis failed",
            error_message=str(exc),
            finished_at=datetime.utcnow(),
        )
        raise
    finally:
        try:
            Path(upload.local_processing_path).unlink(missing_ok=True)
        except Exception:
            pass


@router.post("/jobs", response_model=ValidationJobResponse)
async def create_validation_job(
    pdf: UploadFile = File(..., description="PDF file"),
    rules_json: str | None = Form(None, description="Selected rules JSON"),
    db: Session = Depends(get_db),
) -> ValidationJobResponse:
    settings = get_settings()
    document_service = DocumentService(storage=get_storage_provider(settings), workdir=settings.LOCAL_WORKDIR)
    upload = document_service.prepare_upload_for_processing(filename=pdf.filename or "document.pdf", content=await pdf.read())
    service = ValidationService()
    selected_rules = service.rule_service.load_rules(rules_json_str=rules_json)
    document = DocumentRepository(db).create(
        external_id=upload.document_id,
        original_filename=upload.filename,
        storage_path=upload.storage_path,
        public_url=upload.public_url,
    )
    job = validation_job_service.start_job(
        pdf_path=upload.local_processing_path,
        source_filename=upload.filename,
        source_pdf_url=upload.public_url,
        rules_json_str=rules_json,
        document_id=document.id,
        selected_rules=selected_rules,
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
