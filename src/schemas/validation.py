from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ExtractedTableSchema(BaseModel):
    index: int = Field(..., description="1-based table index within the page.")
    rows: list[list[str]] = Field(default_factory=list, description="Normalized table rows extracted from the page.")


class PageExtractionSchema(BaseModel):
    page: int = Field(..., description="1-based page number from the PDF.")
    text: str = Field(default="", description="Raw text extracted from the page.")
    tables: list[ExtractedTableSchema] = Field(default_factory=list, description="Structured tables extracted from the page.")
    char_count: int = Field(default=0, description="Character count of extracted page text.")


class AnalysisMetricSchema(BaseModel):
    label: str
    value: str
    detail: Optional[str] = None


class PageAnalysisSchema(BaseModel):
    page: int
    observations: list[str] = Field(default_factory=list)


class RuleAssessmentSchema(BaseModel):
    rule_id: str
    rule_name: str
    matched_pages: list[int] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class DocumentAnalysisSchema(BaseModel):
    overview: list[AnalysisMetricSchema] = Field(default_factory=list)
    selected_rule_count: int = 0
    rule_assessments: list[RuleAssessmentSchema] = Field(default_factory=list)
    page_observations: list[PageAnalysisSchema] = Field(default_factory=list)


class DocumentValidationResponse(BaseModel):
    document_id: str
    page_count: int = Field(default=0, description="Total number of pages processed.")
    source_filename: Optional[str] = None
    source_pdf_url: Optional[str] = None
    analysis: DocumentAnalysisSchema = Field(default_factory=DocumentAnalysisSchema)
    pages: list[PageExtractionSchema] = Field(default_factory=list)
