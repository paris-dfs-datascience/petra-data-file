from __future__ import annotations

import os
from pathlib import Path

import fitz


class PdfRenderer:
    def render(self, pdf_path: str, out_dir: str, dpi: int = 200, image_format: str = "png") -> list[str]:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        doc = fitz.open(pdf_path)
        paths: list[str] = []
        try:
            for i, page in enumerate(doc):
                mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                fname = os.path.join(out_dir, f"page_{i + 1:04d}.{image_format}")
                pix.save(fname)
                paths.append(fname)
        finally:
            doc.close()
        return paths
