from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw


def image_path_to_base64_data_url(path: str) -> str:
    p = Path(path)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    b = p.read_bytes()
    enc = base64.b64encode(b).decode("utf-8")
    return f"data:{mime};base64,{enc}"


def image_path_to_base64_data_url_with_centerline(path: str) -> str:
    """Generate a base64 data URL with a thin, low-opacity red vertical center line overlay.
    
    The line is drawn at x = floor(width/2), 2px wide, with RGBA (255, 0, 0, 120) (~50% opacity).
    """
    p = Path(path)
    
    # Open image and convert to RGBA to support transparency blending
    img = Image.open(p).convert("RGBA")
    width, height = img.size
    
    # Create a transparent overlay for the line
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Draw vertical center line: x = floor(width/2), 2px wide, low opacity red
    center_x = width // 2
    line_color = (255, 0, 0, 180)  # RGBA: red with ~70% opacity
    draw.line([(center_x, 0), (center_x, height)], fill=line_color, width=2)
    
    # Composite the overlay onto the original image
    img_with_line = Image.alpha_composite(img, overlay)
    
    # Convert back to RGB (PNG doesn't require alpha for final output)
    img_final = img_with_line.convert("RGB")
    
    # Export to PNG bytes
    buffer = BytesIO()
    img_final.save(buffer, format="PNG")
    png_bytes = buffer.getvalue()
    
    enc = base64.b64encode(png_bytes).decode("utf-8")
    return f"data:image/png;base64,{enc}"


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)
