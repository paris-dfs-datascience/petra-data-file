from pathlib import Path

from src.main import _run_pipeline


def test_pipeline_returns_page_structure():
    """Test that the pipeline returns the current extraction and analysis structure."""
    sample_pdf = Path("tests/sample.pdf")
    if not sample_pdf.exists():
        return

    result = _run_pipeline(pdf_path=str(sample_pdf))

    assert "document_id" in result
    assert "analysis" in result
    assert "pages" in result
    assert isinstance(result["pages"], list)
    assert "rule_assessments" in result["analysis"]

    if result["pages"]:
        page = result["pages"][0]
        assert "page" in page
        assert "text" in page
        assert "tables" in page
        assert "char_count" in page

    if result["analysis"]["rule_assessments"]:
        rule = result["analysis"]["rule_assessments"][0]
        assert "rule_id" in rule
        assert "rule_name" in rule
        assert "analysis_type" in rule
        assert "execution_status" in rule
        assert "verdict" in rule
        assert "summary" in rule
        assert "reasoning" in rule
        assert "citations" in rule


def test_placeholder():
    """Placeholder test to ensure pytest runs."""
    assert True
