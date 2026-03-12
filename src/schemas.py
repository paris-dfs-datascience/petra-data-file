from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class Rule(BaseModel):
    id: str
    name: str
    query: str
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    severity: Optional[str] = None


class Citation(BaseModel):
    page: int = Field(..., description="1-based page number from the PDF.")
    evidence: Optional[str] = Field(None, description="Short evidence text or heading visible in the image.")


class PreviewImage(BaseModel):
    page: int = Field(..., description="1-based page number from the PDF.")
    image_data_url: str = Field(..., description="Base64 data URL of the preview image.")


class RuleResult(BaseModel):
    rule_id: str
    rule_name: str
    status: str = Field(..., pattern="^(pass|fail)$")
    reasoning: str
    citations: List[Citation] = Field(default_factory=list)
    preview_images: List[PreviewImage] = Field(default_factory=list, description="Pages the agent reviewed for this rule.")


class PageResult(BaseModel):
    page: int = Field(..., description="1-based page number from the PDF.")
    image_data_url: str = Field(..., description="Base64 data URL of the page image.")
    image_data_url_centerline: Optional[str] = Field(None, description="Base64 data URL of the page image with center guide line overlay.")
    rules: List[RuleResult] = Field(default_factory=list, description="Rule evaluation results for this page.")


class DocumentResult(BaseModel):
    document_id: str
    pages: List[PageResult] = Field(default_factory=list, description="Per-page validation results.")
    results: Optional[List[RuleResult]] = Field(default=None, description="Deprecated: kept for backward compatibility.")
