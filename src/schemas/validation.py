from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CitationSchema(BaseModel):
    page: int = Field(..., description="1-based page number from the PDF.")
    evidence: Optional[str] = Field(None, description="Short evidence text or heading visible in the image.")


class PreviewImageSchema(BaseModel):
    page: int = Field(..., description="1-based page number from the PDF.")
    image_data_url: str = Field(..., description="Base64 data URL of the preview image.")


class RuleResultSchema(BaseModel):
    rule_id: str
    rule_name: str
    status: str = Field(..., pattern="^(pass|fail)$")
    reasoning: str
    citations: list[CitationSchema] = Field(default_factory=list)
    preview_images: list[PreviewImageSchema] = Field(default_factory=list)


class PageResultSchema(BaseModel):
    page: int = Field(..., description="1-based page number from the PDF.")
    image_data_url: str = Field(..., description="Base64 data URL of the page image.")
    image_data_url_centerline: Optional[str] = Field(None, description="Page image with center guide line overlay.")
    rules: list[RuleResultSchema] = Field(default_factory=list)


class DocumentValidationResponse(BaseModel):
    document_id: str
    pages: list[PageResultSchema] = Field(default_factory=list)
    results: Optional[list[RuleResultSchema]] = Field(default=None, description="Deprecated compatibility field.")
