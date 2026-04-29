"""Unit tests for the double-underline hint extraction and vector-data text formatting."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.pdf_renderer import PdfRenderer
from src.providers.analysis_result import build_vector_data_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rect(y0: float, y1: float, x0: float, x1: float) -> SimpleNamespace:
    return SimpleNamespace(y0=y0, y1=y1, x0=x0, x1=x1)


def _drawing(y0: float, y1: float, x0: float, x1: float) -> dict:
    return {"rect": _rect(y0, y1, x0, x1)}


def _run_hints(drawings: list[dict], page_height: float = 792.0) -> list[dict]:
    """Run extract_double_underline_hints with a mocked fitz document."""
    mock_page = MagicMock()
    mock_page.rect.height = page_height
    mock_page.get_drawings.return_value = drawings

    mock_doc = MagicMock()
    mock_doc.__getitem__.return_value = mock_page

    mock_fitz = MagicMock()
    mock_fitz.open.return_value = mock_doc

    with patch("src.pipeline.pdf_renderer.fitz", mock_fitz):
        return PdfRenderer().extract_double_underline_hints("any.pdf", 0)


# ---------------------------------------------------------------------------
# Tests for PdfRenderer.extract_double_underline_hints
# ---------------------------------------------------------------------------


class TestExtractDoubleUnderlineHints:
    # --- basic cases ---

    def test_no_drawings_returns_empty(self):
        assert _run_hints([]) == []

    def test_single_line_no_pair(self):
        assert _run_hints([_drawing(100.0, 100.5, 50.0, 300.0)]) == []

    def test_canonical_double_underline_detected(self):
        hints = _run_hints([
            _drawing(100.0, 100.5, 50.0, 300.0),
            _drawing(101.5, 102.0, 50.0, 300.0),
        ])
        assert len(hints) == 1
        assert "y_fraction" in hints[0]

    def test_y_fraction_calculation(self):
        # center_y = (400.0 + 402.0) / 2 = 401.0; fraction = round(401.0 / 800.0, 3)
        hints = _run_hints(
            [
                _drawing(400.0, 400.5, 50.0, 300.0),
                _drawing(401.5, 402.0, 50.0, 300.0),
            ],
            page_height=800.0,
        )
        assert hints == [{"y_fraction": round(401.0 / 800.0, 3)}]

    # --- gap-range filtering ---

    def test_gap_well_above_upper_bound_not_detected(self):
        # gap ≈ 101pt — far exceeds the 3pt limit
        assert _run_hints([
            _drawing(100.0, 100.5, 50.0, 300.0),
            _drawing(201.5, 202.0, 50.0, 300.0),
        ]) == []

    def test_gap_just_above_upper_bound_not_detected(self):
        # gap = 103.6 - 100.5 = 3.1 → break
        assert _run_hints([
            _drawing(100.0, 100.5, 50.0, 300.0),
            _drawing(103.6, 104.0, 50.0, 300.0),
        ]) == []

    def test_gap_at_upper_boundary_detected(self):
        # gap = 103.5 - 100.5 = 3.0 → exactly at limit, not > 3 → detected
        hints = _run_hints([
            _drawing(100.0, 100.5, 50.0, 300.0),
            _drawing(103.5, 104.0, 50.0, 300.0),
        ])
        assert len(hints) == 1

    def test_gap_inside_detection_window_detected(self):
        # gap = 101.0 - 100.5 = 0.5pt — inside the [0.3, 3.0] detection window.
        # Using exact IEEE-754 values (0.5 = 1/2, 100.5 / 101.0 both exact) avoids
        # float precision ambiguity at the 0.3 boundary.
        hints = _run_hints([
            _drawing(100.0, 100.5, 50.0, 300.0),
            _drawing(101.0, 101.5, 50.0, 300.0),
        ])
        assert len(hints) == 1

    # --- Stage-1 collapse (coincident paths) ---

    def test_coincident_paths_collapsed_to_single_logical_line(self):
        # gap = 100.5 - 100.5 = 0.0 ≤ 0.1 → Stage 1 merges into one logical line → no pair
        assert _run_hints([
            _drawing(100.0, 100.5, 50.0, 300.0),
            _drawing(100.5, 101.0, 50.0, 300.0),
        ]) == []

    def test_stage1_collapse_threshold_boundary(self):
        # gap = 0.1 → not > 0.1 → still collapsed
        assert _run_hints([
            _drawing(100.0, 100.5, 50.0, 300.0),
            _drawing(100.6, 101.1, 50.0, 300.0),
        ]) == []

    def test_three_coincident_paths_all_collapsed(self):
        # Each successive gap ≤ 0.1 → all three merge into one logical line → no pair
        assert _run_hints([
            _drawing(100.0, 100.5, 50.0, 300.0),
            _drawing(100.55, 101.0, 50.0, 300.0),
            _drawing(101.05, 101.5, 50.0, 300.0),
        ]) == []

    def test_gap_between_stage1_and_stage2_threshold_not_detected(self):
        # gap = 100.65 - 100.5 = 0.15 — above Stage-1 collapse limit (0.1) but below
        # Stage-2 detection floor (0.3) → skipped by Stage 2
        assert _run_hints([
            _drawing(100.0, 100.5, 50.0, 300.0),
            _drawing(100.65, 101.15, 50.0, 300.0),
        ]) == []

    # --- x-overlap filtering ---

    def test_insufficient_x_overlap_not_detected(self):
        # overlap=70, span=100 → ratio=0.70, not > 0.70 → not detected
        assert _run_hints([
            _drawing(100.0, 100.5, 0.0, 100.0),
            _drawing(101.5, 102.0, 30.0, 100.0),
        ]) == []

    def test_sufficient_x_overlap_detected(self):
        # overlap=71, span=100 → ratio=0.71 > 0.70 → detected
        hints = _run_hints([
            _drawing(100.0, 100.5, 0.0, 100.0),
            _drawing(101.5, 102.0, 29.0, 100.0),
        ])
        assert len(hints) == 1

    def test_zero_x_overlap_not_detected(self):
        # Lines on non-overlapping x-ranges → overlap ≤ 0 → not detected
        assert _run_hints([
            _drawing(100.0, 100.5, 0.0, 100.0),
            _drawing(101.5, 102.0, 200.0, 400.0),
        ]) == []

    # --- rect-filter edge cases ---

    def test_rect_with_height_equal_to_threshold_filtered(self):
        # height = 3.0, condition is < 3 → filtered out
        assert _run_hints([{"rect": _rect(100.0, 103.0, 50.0, 300.0)}]) == []

    def test_rect_with_width_equal_to_threshold_filtered(self):
        # width = 10.0, condition is > 10 → filtered out
        assert _run_hints([{"rect": _rect(100.0, 100.5, 50.0, 60.0)}]) == []

    def test_drawing_without_rect_key_ignored(self):
        assert _run_hints([{"color": (0, 0, 0)}]) == []

    def test_drawing_with_none_rect_ignored(self):
        assert _run_hints([{"rect": None}]) == []

    # --- multiple pairs ---

    def test_multiple_independent_pairs_both_detected(self):
        hints = _run_hints([
            _drawing(100.0, 100.5, 50.0, 300.0),
            _drawing(101.5, 102.0, 50.0, 300.0),  # pair 1
            _drawing(200.0, 200.5, 50.0, 300.0),
            _drawing(201.5, 202.0, 50.0, 300.0),  # pair 2
        ])
        assert len(hints) == 2

    def test_each_line_used_in_at_most_one_pair(self):
        # Three lines: only the first two form a valid pair; the third is too far from
        # both to form another pair with any already-used line.
        hints = _run_hints([
            _drawing(100.0, 100.5, 50.0, 300.0),
            _drawing(101.5, 102.0, 50.0, 300.0),  # pair with line 0
            _drawing(103.0, 103.5, 50.0, 300.0),  # gap from line 1 = 1.0pt → valid pair candidate
        ])
        # Line 1 is consumed by the first pair; line 2 has no remaining partner.
        assert len(hints) == 1

    # --- error handling ---

    def test_exception_from_fitz_returns_empty_list(self):
        mock_fitz = MagicMock()
        mock_fitz.open.side_effect = RuntimeError("file not found")
        with patch("src.pipeline.pdf_renderer.fitz", mock_fitz):
            result = PdfRenderer().extract_double_underline_hints("missing.pdf", 0)
        assert result == []


# ---------------------------------------------------------------------------
# Tests for build_vector_data_text
# ---------------------------------------------------------------------------


class TestBuildVectorDataText:
    def test_hints_none_returns_empty_string(self):
        assert build_vector_data_text({"double_underline_hints": None}) == ""

    def test_key_absent_returns_empty_string(self):
        assert build_vector_data_text({}) == ""

    def test_empty_hints_list_returns_no_detection_message(self):
        result = build_vector_data_text({"double_underline_hints": []})
        assert "VECTOR DATA" in result
        assert "No double underline" in result

    def test_single_hint_position_appears_in_output(self):
        result = build_vector_data_text({"double_underline_hints": [{"y_fraction": 0.75}]})
        assert "VECTOR DATA" in result
        assert "0.75" in result

    def test_multiple_hint_positions_all_appear_in_output(self):
        result = build_vector_data_text({"double_underline_hints": [{"y_fraction": 0.5}, {"y_fraction": 0.85}]})
        assert "0.5" in result
        assert "0.85" in result

    def test_detected_output_includes_authoritative_label(self):
        result = build_vector_data_text({"double_underline_hints": [{"y_fraction": 0.6}]})
        assert "authoritative" in result

    def test_no_detection_output_includes_authoritative_label(self):
        result = build_vector_data_text({"double_underline_hints": []})
        assert "authoritative" in result

    @pytest.mark.parametrize("y_frac", [0.0, 0.5, 0.999])
    def test_y_fraction_value_preserved_exactly(self, y_frac: float):
        result = build_vector_data_text({"double_underline_hints": [{"y_fraction": y_frac}]})
        assert str(y_frac) in result
