from __future__ import annotations

import re
from statistics import mean, median

import pdfplumber

from src.core.config import AppYaml
from src.pipeline.page_classifier import classify_page


_INTRA_NUMBER_SPACE_PATTERNS = (
    re.compile(r"(?<=\d) (?=\d{0,2},\d{3})"),
    re.compile(r"(?<=\d) (?=\d{1,3}\.\d)"),
    re.compile(r"(?<=\d)\s+(?=%)"),
)


def _join_split_numbers(text: str) -> str:
    if not text:
        return text
    for pattern in _INTRA_NUMBER_SPACE_PATTERNS:
        text = pattern.sub("", text)
    return text


def _normalize_cell(value: object) -> str:
    if value is None:
        return ""
    return _join_split_numbers(str(value).strip())


def _as_float(value: object) -> float:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def _ranges_overlap(start_a: float, end_a: float, start_b: float, end_b: float, tolerance: float = 2.0) -> bool:
    return not (end_a < start_b - tolerance or end_b < start_a - tolerance)


def _line_intersects_table(line: dict, table_regions: list[dict]) -> bool:
    for region in table_regions:
        if _ranges_overlap(line["x0"], line["x1"], region["x0"], region["x1"]) and _ranges_overlap(
            line["top"],
            line["bottom"],
            region["top"],
            region["bottom"],
        ):
            return True
    return False


def _centering_tolerance(page_width: float, non_space_char_count: int) -> float:
    base_tolerance = max(10.0, min(18.0, round(page_width * 0.02, 2)))
    if non_space_char_count >= 28:
        return round(max(8.0, base_tolerance - 3.0), 2)
    if non_space_char_count >= 18:
        return round(max(9.0, base_tolerance - 2.0), 2)
    if non_space_char_count <= 6:
        return round(min(20.0, base_tolerance + 2.0), 2)
    return round(base_tolerance, 2)


def _median_or_zero(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(float(median(values)), 2)


def _median_absolute_deviation(values: list[float], reference: float) -> float:
    if not values:
        return 0.0
    return round(float(median(abs(value - reference) for value in values)), 2)


def _summarize_line(words: list[dict], page_width: float, table_regions: list[dict]) -> dict:
    ordered_words = sorted(words, key=lambda item: _as_float(item.get("x0")))
    text_parts = [_normalize_cell(item.get("text")) for item in ordered_words]
    text = " ".join(part for part in text_parts if part).strip()
    x0 = min(_as_float(item.get("x0")) for item in ordered_words)
    x1 = max(_as_float(item.get("x1")) for item in ordered_words)
    top = min(_as_float(item.get("top")) for item in ordered_words)
    bottom = max(_as_float(item.get("bottom")) for item in ordered_words)
    width = round(max(0.0, x1 - x0), 2)
    center_x = round(x0 + (width / 2.0), 2)
    page_center_x = round(page_width / 2.0, 2)
    font_sizes = [_as_float(item.get("size")) for item in ordered_words if item.get("size") is not None]
    non_space_char_count = len(text.replace(" ", ""))
    center_offset = round(center_x - page_center_x, 2)
    abs_center_offset = round(abs(center_offset), 2)
    right_margin = round(max(0.0, page_width - x1), 2)
    margin_delta = round(abs(x0 - right_margin), 2)
    centering_tolerance_px = _centering_tolerance(page_width, non_space_char_count)
    line = {
        "text": text,
        "x0": x0,
        "x1": x1,
        "top": top,
        "bottom": bottom,
        "width": width,
        "center_x": center_x,
        "page_center_x": page_center_x,
        "center_offset": center_offset,
        "abs_center_offset": abs_center_offset,
        "left_margin": x0,
        "right_margin": right_margin,
        "margin_delta": margin_delta,
        "center_offset_ratio": round(abs_center_offset / page_width, 4) if page_width else 0.0,
        "margin_delta_ratio": round(margin_delta / page_width, 4) if page_width else 0.0,
        "word_count": len([part for part in text_parts if part]),
        "non_space_char_count": non_space_char_count,
        "centering_tolerance_px": centering_tolerance_px,
    }
    if font_sizes:
        line["avg_font_size"] = round(mean(font_sizes), 2)
    line["inside_table"] = _line_intersects_table(line, table_regions)
    return line


def _build_alignment_reference(top_lines: list[dict], page_width: float) -> dict:
    reference_lines = [line for line in top_lines if int(line.get("non_space_char_count", 0)) >= 4]
    if not reference_lines:
        reference_lines = list(top_lines)
    if not reference_lines:
        return {
            "reference_line_count": 0,
            "dominant_alignment": "unknown",
            "left_reference": 0.0,
            "center_reference": 0.0,
            "right_reference": 0.0,
            "left_consistency_score": 0.0,
            "center_consistency_score": 0.0,
            "right_consistency_score": 0.0,
            "group_tolerance_px": max(10.0, min(18.0, round(page_width * 0.02, 2))) if page_width else 10.0,
        }

    left_values = [float(line.get("left_margin", 0.0)) for line in reference_lines]
    center_values = [float(line.get("center_offset", 0.0)) for line in reference_lines]
    right_values = [float(line.get("right_margin", 0.0)) for line in reference_lines]

    left_reference = _median_or_zero(left_values)
    center_reference = _median_or_zero(center_values)
    right_reference = _median_or_zero(right_values)

    left_consistency_score = _median_absolute_deviation(left_values, left_reference)
    center_consistency_score = _median_absolute_deviation(center_values, center_reference)
    right_consistency_score = _median_absolute_deviation(right_values, right_reference)

    consistency_scores = {
        "left": left_consistency_score,
        "center": center_consistency_score,
        "right": right_consistency_score,
    }
    dominant_alignment = min(consistency_scores, key=consistency_scores.get)
    base_tolerance = max(10.0, min(18.0, round(page_width * 0.02, 2))) if page_width else 10.0
    group_tolerance_px = round(max(base_tolerance, consistency_scores[dominant_alignment] + 3.0), 2)

    return {
        "reference_line_count": len(reference_lines),
        "dominant_alignment": dominant_alignment,
        "left_reference": left_reference,
        "center_reference": center_reference,
        "right_reference": right_reference,
        "left_consistency_score": left_consistency_score,
        "center_consistency_score": center_consistency_score,
        "right_consistency_score": right_consistency_score,
        "group_tolerance_px": group_tolerance_px,
    }


def _apply_alignment_reference(line: dict, alignment_reference: dict) -> dict:
    updated_line = dict(line)
    left_alignment_delta = round(abs(float(line.get("left_margin", 0.0)) - float(alignment_reference.get("left_reference", 0.0))), 2)
    center_alignment_delta = round(
        abs(float(line.get("center_offset", 0.0)) - float(alignment_reference.get("center_reference", 0.0))),
        2,
    )
    right_alignment_delta = round(
        abs(float(line.get("right_margin", 0.0)) - float(alignment_reference.get("right_reference", 0.0))),
        2,
    )
    delta_map = {
        "left": left_alignment_delta,
        "center": center_alignment_delta,
        "right": right_alignment_delta,
    }
    best_alignment = min(delta_map, key=delta_map.get)
    updated_line["left_alignment_delta"] = left_alignment_delta
    updated_line["center_alignment_delta"] = center_alignment_delta
    updated_line["right_alignment_delta"] = right_alignment_delta
    updated_line["best_alignment"] = best_alignment
    updated_line["best_alignment_delta"] = round(delta_map[best_alignment], 2)
    updated_line["alignment_tolerance_px"] = round(
        max(
            float(line.get("centering_tolerance_px", 0.0) or 0.0),
            float(alignment_reference.get("group_tolerance_px", 0.0) or 0.0),
        ),
        2,
    )
    return updated_line


def _summarize_top_lines(page: pdfplumber.page.Page, table_regions: list[dict]) -> dict:
    page_width = _as_float(page.width)
    page_height = _as_float(page.height)
    words = page.extract_words(
        use_text_flow=True,
        keep_blank_chars=False,
        extra_attrs=["size"],
    ) or []
    if not words:
        return {
            "page_width": page_width,
            "page_height": page_height,
            "top_lines": [],
        }

    grouped_lines: list[dict] = []
    current_words: list[dict] = []
    current_midline: float | None = None

    for word in sorted(words, key=lambda item: (_as_float(item.get("top")), _as_float(item.get("x0")))):
        if not _normalize_cell(word.get("text")):
            continue
        top = _as_float(word.get("top"))
        bottom = _as_float(word.get("bottom"))
        midline = round((top + bottom) / 2.0, 2)
        if current_words and current_midline is not None and abs(midline - current_midline) > 3.0:
            grouped_lines.append(_summarize_line(current_words, page_width, table_regions))
            current_words = [word]
        else:
            current_words.append(word)

        current_midline = round(
            mean((_as_float(item.get("top")) + _as_float(item.get("bottom"))) / 2.0 for item in current_words),
            2,
        )

    if current_words:
        grouped_lines.append(_summarize_line(current_words, page_width, table_regions))

    top_region_limit = round(page_height * 0.35, 2) if page_height else 0.0
    candidate_lines = [
        line
        for line in grouped_lines
        if line.get("text") and not line.get("inside_table") and (not top_region_limit or line.get("top", 0.0) <= top_region_limit)
    ]
    if not candidate_lines:
        candidate_lines = [line for line in grouped_lines if line.get("text") and not line.get("inside_table")]
    if not candidate_lines:
        candidate_lines = [line for line in grouped_lines if line.get("text")]

    top_lines = []
    for line in candidate_lines[:12]:
        top_lines.append(
            {
                "text": line.get("text", ""),
                "x0": line.get("x0", 0.0),
                "x1": line.get("x1", 0.0),
                "top": line.get("top", 0.0),
                "bottom": line.get("bottom", 0.0),
                "width": line.get("width", 0.0),
                "center_x": line.get("center_x", 0.0),
                "page_center_x": line.get("page_center_x", 0.0),
                "center_offset": line.get("center_offset", 0.0),
                "abs_center_offset": line.get("abs_center_offset", 0.0),
                "left_margin": line.get("left_margin", 0.0),
                "right_margin": line.get("right_margin", 0.0),
                "margin_delta": line.get("margin_delta", 0.0),
                "center_offset_ratio": line.get("center_offset_ratio", 0.0),
                "margin_delta_ratio": line.get("margin_delta_ratio", 0.0),
                "word_count": line.get("word_count", 0),
                "non_space_char_count": line.get("non_space_char_count", 0),
                "centering_tolerance_px": line.get("centering_tolerance_px", 0.0),
                "avg_font_size": line.get("avg_font_size", 0.0),
            }
        )

    alignment_reference = _build_alignment_reference(top_lines, page_width)
    top_lines = [_apply_alignment_reference(line, alignment_reference) for line in top_lines]

    return {
        "page_width": page_width,
        "page_height": page_height,
        "alignment_reference": alignment_reference,
        "top_lines": top_lines,
    }


class PdfExtractor:
    def __init__(self, app_config: AppYaml | None = None) -> None:
        self.app_config = app_config

    def _extract_page_text(self, page: pdfplumber.page.Page) -> str:
        pdf_config = self.app_config.pdf if self.app_config else None
        use_layout = pdf_config.text_layout if pdf_config else True
        x_density = pdf_config.text_x_density if pdf_config else 7.25
        y_density = pdf_config.text_y_density if pdf_config else 13.0
        raw = page.extract_text(layout=use_layout, x_density=x_density, y_density=y_density) or ""
        return _join_split_numbers(raw)

    def extract(self, pdf_path: str) -> list[dict]:
        pages: list[dict] = []
        with pdfplumber.open(pdf_path) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = self._extract_page_text(page)
                detected_tables = page.find_tables() or []
                tables = []
                table_regions = []
                for table_index, table in enumerate(detected_tables, start=1):
                    bbox = getattr(table, "bbox", None)
                    if bbox and len(bbox) == 4:
                        table_regions.append(
                            {
                                "x0": _as_float(bbox[0]),
                                "top": _as_float(bbox[1]),
                                "x1": _as_float(bbox[2]),
                                "bottom": _as_float(bbox[3]),
                            }
                        )
                    rows = [[_normalize_cell(cell) for cell in row] for row in (table.extract() or [])]
                    if not rows:
                        continue
                    tables.append(
                        {
                            "index": table_index,
                            "rows": rows,
                        }
                    )

                page_dict = {
                    "page": index,
                    "text": text,
                    "tables": tables,
                    "char_count": len(text),
                    "layout_summary": _summarize_top_lines(page, table_regions),
                }
                page_dict["page_type"] = classify_page(page_dict)
                pages.append(page_dict)
        return pages
