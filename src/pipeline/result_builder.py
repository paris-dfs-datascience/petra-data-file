from __future__ import annotations

import re

from src.schemas.validation import DocumentAnalysisSchema, DocumentValidationResponse


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _keywords_from_rule(rule: dict) -> list[str]:
    raw = " ".join(
        [
            rule.get("name", ""),
            rule.get("query", ""),
            rule.get("description", ""),
            rule.get("acceptance_criteria", ""),
        ]
    )
    tokens = re.findall(r"[a-zA-Z]{4,}", raw.lower())
    seen: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.append(token)
    return seen[:12]


def build_document_analysis(pages: list[dict], selected_rules: list[dict] | None = None) -> dict:
    total_chars = sum(page.get("char_count", 0) for page in pages)
    total_tables = sum(len(page.get("tables", [])) for page in pages)
    pages_with_text = sum(1 for page in pages if (page.get("text") or "").strip())
    pages_with_tables = sum(1 for page in pages if page.get("tables"))
    selected_rules = selected_rules or []

    overview = [
        {"label": "Pages", "value": str(len(pages)), "detail": "Total pages processed from the PDF."},
        {"label": "Pages With Text", "value": str(pages_with_text), "detail": "Pages where pdfplumber extracted non-empty text."},
        {"label": "Pages With Tables", "value": str(pages_with_tables), "detail": "Pages where at least one table was detected."},
        {"label": "Total Characters", "value": str(total_chars), "detail": "Combined extracted character count across all pages."},
        {"label": "Total Tables", "value": str(total_tables), "detail": "Combined number of extracted tables."},
        {"label": "Selected Rules", "value": str(len(selected_rules)), "detail": "Rules enabled for this analysis run."},
    ]

    rule_assessments = []
    for rule in selected_rules:
        keywords = _keywords_from_rule(rule)
        matched_pages: list[int] = []
        notes: list[str] = []
        for page in pages:
            page_text = _normalize(page.get("text", ""))
            if any(keyword in page_text for keyword in keywords):
                matched_pages.append(page.get("page", 0))
        if matched_pages:
            notes.append(f"Keyword overlap found on page(s): {', '.join(str(page) for page in matched_pages)}.")
        else:
            notes.append("No obvious keyword overlap found in extracted text.")
        if keywords:
            notes.append(f"Keywords used: {', '.join(keywords[:6])}.")
        rule_assessments.append(
            {
                "rule_id": rule.get("id", ""),
                "rule_name": rule.get("name", rule.get("id", "")),
                "matched_pages": matched_pages,
                "notes": notes,
            }
        )

    page_observations = []
    for page in pages:
        text = (page.get("text") or "").strip()
        tables = page.get("tables", [])
        observations: list[str] = []
        if text:
            first_line = text.splitlines()[0].strip()
            if first_line:
                observations.append(f"Starts with: {first_line[:160]}")
        else:
            observations.append("No text extracted from this page.")

        if tables:
            observations.append(f"{len(tables)} table(s) detected.")
        else:
            observations.append("No tables detected.")

        page_observations.append({"page": page.get("page", 0), "observations": observations})

    return DocumentAnalysisSchema(
        overview=overview,
        selected_rule_count=len(selected_rules),
        rule_assessments=rule_assessments,
        page_observations=page_observations,
    ).model_dump()


def build_document_result(
    document_id: str,
    pages: list[dict],
    source_filename: str | None = None,
    source_pdf_url: str | None = None,
    selected_rules: list[dict] | None = None,
) -> dict:
    return DocumentValidationResponse(
        document_id=document_id,
        page_count=len(pages),
        source_filename=source_filename,
        source_pdf_url=source_pdf_url,
        analysis=build_document_analysis(pages, selected_rules=selected_rules),
        pages=pages,
    ).model_dump()
