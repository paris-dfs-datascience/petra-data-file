from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.config import get_settings
from src.providers.storage.factory import get_storage_provider
from src.repositories.document_repository import DocumentRepository
from src.schemas.document import DocumentUploadResponse
from src.services.document_service import DocumentService


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(pdf: UploadFile = File(...), db: Session = Depends(get_db)) -> DocumentUploadResponse:
    settings = get_settings()
    service = DocumentService(storage=get_storage_provider(settings), workdir=settings.LOCAL_WORKDIR)
    upload = service.save_upload(filename=pdf.filename or "document.pdf", content=await pdf.read())
    DocumentRepository(db).create(
        external_id=upload.document_id,
        original_filename=upload.filename,
        storage_path=upload.storage_path,
        public_url=upload.public_url,
    )
    return upload
