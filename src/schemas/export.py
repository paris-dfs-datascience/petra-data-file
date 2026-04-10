from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from src.schemas.validation import DocumentAnalysisSchema


class ExportPdfRequest(BaseModel):
    document_id: str
    source_filename: Optional[str] = None
    page_count: int = 0
    cover_sheet_text: str = Field(default="", description="Free-text cover page content provided by the user.")
    analysis: DocumentAnalysisSchema = Field(default_factory=DocumentAnalysisSchema)
