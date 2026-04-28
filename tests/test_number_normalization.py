"""Unit tests for the pdfplumber number-artifact normalization helper."""

import pytest

from src.pipeline.pdf_extractor import _fix_number_artifacts


@pytest.mark.parametrize(
    "raw, expected",
    [
        # Thousands-split artifacts
        ("8 9,674", "89,674"),
        ("1 0,358,013", "10,358,013"),
        ("2 59,479", "259,479"),
        ("1 86,554", "186,554"),
        ("5 ,388", "5,388"),
        # Decimal-split artifact
        ("1 03.29 %", "103.29%"),
        # Trailing space before percent only
        ("29.5 %", "29.5%"),
        # Multi-digit thousands (no split needed)
        ("1,234,567", "1,234,567"),
        # Two unrelated column-header numbers — must NOT be joined
        ("2024 2025", "2024 2025"),
        # Side-by-side values separated by multiple spaces — must NOT be joined
        ("12,345  6,789", "12,345  6,789"),
        # Negative in parentheses — must NOT collapse
        ("(1 86,554)", "(186,554)"),
        # Plain text label with spaces — unchanged
        ("Page 5 of 10", "Page 5 of 10"),
    ],
)
def test_fix_number_artifacts(raw: str, expected: str) -> None:
    assert _fix_number_artifacts(raw) == expected
