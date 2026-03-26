from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from src.schemas.validation import DocumentValidationResponse


def image_path_to_base64_data_url(path: str) -> str:
    p = Path(path)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    enc = base64.b64encode(p.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{enc}"


def image_path_to_base64_data_url_with_centerline(path: str) -> str:
    p = Path(path)
    img = Image.open(p).convert("RGBA")
    width, height = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    center_x = width // 2
    draw.line([(center_x, 0), (center_x, height)], fill=(255, 0, 0, 180), width=2)

    merged = Image.alpha_composite(img, overlay).convert("RGB")
    buffer = BytesIO()
    merged.save(buffer, format="PNG")
    enc = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{enc}"


def build_document_result(document_id: str, pages: list[dict]) -> dict:
    return DocumentValidationResponse(document_id=document_id, pages=pages).model_dump()
