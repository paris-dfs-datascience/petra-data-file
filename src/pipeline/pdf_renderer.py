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

    def extract_double_underline_hints(self, pdf_path: str, page_index: int) -> list[dict] | None:
        """Return y-positions (as page-height fractions) of double-underline line pairs found in PDF vector data.

        Returns:
            - list of {"y_fraction": float} entries, one per detected pair (empty list if none detected)
            - None if extraction failed (e.g. corrupted PDF, fitz error) — distinct from "no pairs found"
              so callers can avoid presenting algorithmic absence as authoritative when the algorithm
              didn't actually run.

        Many PDF generators render each visible line as two coincident (0pt gap) paths — a rendering artifact.
        The algorithm therefore works in two stages:
          1. Collapse coincident paths (gap <= 0.1pt) into single logical lines.
          2. Detect double underlines as pairs of logical lines 0.3–3pt apart (the actual accounting separation).
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_index]
            page_height = page.rect.height

            raw = []
            for d in page.get_drawings():
                r = d.get("rect")
                if r and (r.y1 - r.y0) < 3 and (r.x1 - r.x0) > 10:
                    raw.append({"y0": r.y0, "y1": r.y1, "x0": r.x0, "x1": r.x1})

            raw.sort(key=lambda l: l["y0"])

            # Stage 1: collapse coincident/near-coincident paths into logical lines
            logical: list[dict] = []
            skip: set[int] = set()
            for i, a in enumerate(raw):
                if i in skip:
                    continue
                merged = dict(a)
                for j, b in enumerate(raw[i + 1 :], start=i + 1):
                    if j in skip:
                        continue
                    if b["y0"] - merged["y1"] > 0.1:
                        break
                    merged["y0"] = min(merged["y0"], b["y0"])
                    merged["y1"] = max(merged["y1"], b["y1"])
                    merged["x0"] = min(merged["x0"], b["x0"])
                    merged["x1"] = max(merged["x1"], b["x1"])
                    skip.add(j)
                logical.append(merged)

            # Stage 2: find pairs of logical lines 0.3–3pt apart — the accounting double-underline gap.
            # 0.3pt minimum excludes truly coincident residuals; single underlines are 13pt+ apart after Stage 1.
            hints = []
            used: set[int] = set()
            for i, a in enumerate(logical):
                if i in used:
                    continue
                for j, b in enumerate(logical[i + 1 :], start=i + 1):
                    if j in used:
                        continue
                    gap = b["y0"] - a["y1"]
                    if gap > 3:
                        break
                    if gap < 0.3:
                        continue
                    overlap = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
                    span = max(a["x1"] - a["x0"], b["x1"] - b["x0"])
                    if span > 0 and overlap / span > 0.7:
                        hints.append({"y_fraction": round((a["y0"] + b["y1"]) / 2 / page_height, 3)})
                        used.add(i)
                        used.add(j)
                        break

            doc.close()
            return hints
        except Exception:
            return None

    def _add_page_frame(self, image_path: str) -> None:
        image = Image.open(image_path).convert("RGB")
        pad_x = max(32, image.width // 20)
        pad_y = max(32, image.height // 20)
        framed = ImageOps.expand(image, border=(pad_x, pad_y, pad_x, pad_y), fill="white")
        framed = ImageOps.expand(framed, border=2, fill="#d1d5db")
        framed.save(image_path)
