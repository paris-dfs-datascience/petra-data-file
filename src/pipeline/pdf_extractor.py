from __future__ import annotations

import pdfplumber


def _normalize_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


class PdfExtractor:
    def extract(self, pdf_path: str) -> list[dict]:
        pages: list[dict] = []
        with pdfplumber.open(pdf_path) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
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
