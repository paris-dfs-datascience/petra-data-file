from fastapi import APIRouter, File, UploadFile

from src.core.config import get_settings
from src.providers.storage.factory import get_storage_provider
from src.schemas.document import DocumentUploadResponse
from src.services.document_service import DocumentService


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(pdf: UploadFile = File(...)) -> DocumentUploadResponse:
    settings = get_settings()
    service = DocumentService(storage=get_storage_provider(settings), workdir=settings.LOCAL_WORKDIR)
    return service.save_upload(filename=pdf.filename or "document.pdf", content=await pdf.read())
