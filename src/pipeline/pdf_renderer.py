from __future__ import annotations

import os
from pathlib import Path

import fitz
from PIL import Image, ImageOps


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
                self._add_page_frame(fname)
                paths.append(fname)
        finally:
            doc.close()
        return paths

    def _add_page_frame(self, image_path: str) -> None:
        image = Image.open(image_path).convert("RGB")
        pad_x = max(32, image.width // 20)
        pad_y = max(32, image.height // 20)
        framed = ImageOps.expand(image, border=(pad_x, pad_y, pad_x, pad_y), fill="white")
        framed = ImageOps.expand(framed, border=2, fill="#d1d5db")
        framed.save(image_path)
