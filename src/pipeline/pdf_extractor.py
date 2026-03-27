from __future__ import annotations

import pdfplumber

from src.core.config import AppYaml


def _normalize_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


class PdfExtractor:
    def __init__(self, app_config: AppYaml | None = None) -> None:
        self.app_config = app_config

    def _extract_page_text(self, page: pdfplumber.page.Page) -> str:
        pdf_config = self.app_config.pdf if self.app_config else None
        use_layout = pdf_config.text_layout if pdf_config else True
        x_density = pdf_config.text_x_density if pdf_config else 7.25
        y_density = pdf_config.text_y_density if pdf_config else 13.0
        return page.extract_text(layout=use_layout, x_density=x_density, y_density=y_density) or ""

    def extract(self, pdf_path: str) -> list[dict]:
        pages: list[dict] = []
        with pdfplumber.open(pdf_path) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = self._extract_page_text(page)
                raw_tables = page.extract_tables() or []
                tables = []
                for table_index, table in enumerate(raw_tables, start=1):
                    rows = [[_normalize_cell(cell) for cell in row] for row in (table or [])]
                    if not rows:
                        continue
                    tables.append(
                        {
                            "index": table_index,
                            "rows": rows,
                        }
                    )

                pages.append(
                    {
                        "page": index,
                        "text": text,
                        "tables": tables,
                        "char_count": len(text),
                    }
                )
        return pages
