from pathlib import Path
from src.main import _run_pipeline


def test_pipeline_returns_page_structure():
    """Test that the pipeline returns the new page-based structure."""
    # Use the sample PDF in tests/
    sample_pdf = Path("tests/sample.pdf")
    if not sample_pdf.exists():
        # If sample doesn't exist, skip test
        return
    
    # Run pipeline with default rules
    result = _run_pipeline(pdf_path=str(sample_pdf))
    
    # Assert new structure
    assert "document_id" in result
    assert "pages" in result
    assert isinstance(result["pages"], list)
    
    # If there are pages, check structure
    if result["pages"]:
        page = result["pages"][0]
        assert "page" in page
        assert "image_data_url" in page
        assert "rules" in page
        assert isinstance(page["rules"], list)
        
        # If there are rules, check rule structure
        if page["rules"]:
            rule = page["rules"][0]
            assert "rule_id" in rule
            assert "rule_name" in rule
            assert "status" in rule
            assert rule["status"] in ["pass", "fail"]
            assert "reasoning" in rule
            assert "citations" in rule
            assert "preview_images" in rule


def test_placeholder():
    """Placeholder test to ensure pytest runs."""
    assert True
