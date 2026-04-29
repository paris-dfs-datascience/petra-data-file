from __future__ import annotations

from src.pipeline.page_classifier import (
    BALANCE_SHEET,
    COVER_PAGE,
    SCHEDULE_OF_INVESTMENTS,
    STATEMENT_OF_CASH_FLOWS,
    STATEMENT_OF_OPERATIONS,
    classify_page,
    rule_applies_to_page,
)


def _page(text: str = "", page: int = 3, tables: list | None = None) -> dict:
    return {"page": page, "text": text, "tables": tables or []}


def test_classify_balance_sheet_from_text():
    page = _page("Statement of Assets and Liabilities\nTotal assets 100\nTotal liabilities 50\nNet assets 50")
    assert BALANCE_SHEET in classify_page(page)


def test_classify_cash_flows_from_text():
    page = _page("Statement of Cash Flows\nCash flows from operating activities\nNet change in cash")
    assert STATEMENT_OF_CASH_FLOWS in classify_page(page)


def test_classify_statement_of_operations_from_text():
    page = _page("Statement of Operations\nNet investment income\nRealized and unrealized gain on investments")
    assert STATEMENT_OF_OPERATIONS in classify_page(page)


def test_classify_schedule_of_investments_from_text():
    page = _page("Schedule of Investments\nInvestments in securities - 87% of net assets")
    assert SCHEDULE_OF_INVESTMENTS in classify_page(page)


def test_classify_tables_are_scanned_too():
    page = _page(
        text="",
        tables=[{"index": 1, "rows": [["Total assets", "100"], ["Total liabilities", "40"]]}],
    )
    assert BALANCE_SHEET in classify_page(page)


def test_classify_returns_multiple_types_when_combined_page():
    page = _page(
        "Statement of Assets and Liabilities and Statement of Operations\n"
        "Total assets 100\nNet investment income 50"
    )
    types = classify_page(page)
    assert BALANCE_SHEET in types
    assert STATEMENT_OF_OPERATIONS in types


def test_classify_empty_page_returns_empty_list():
    assert classify_page(_page("")) == []


def test_classify_cover_page_by_signals_on_early_page():
    page = _page(
        text="Example Fund L.P.\nFinancial Statements\nFor the year ended December 31, 2024",
        page=1,
        tables=[],
    )
    assert COVER_PAGE in classify_page(page)


def test_classify_unknown_page_returns_empty():
    page = _page("Some generic paragraph about corporate governance with no financial statement keywords.")
    assert classify_page(page) == []


def test_rule_applies_when_section_missing():
    rule = {"id": "FMT-HEADINGS"}
    assert rule_applies_to_page(rule, [BALANCE_SHEET]) is True
    assert rule_applies_to_page(rule, []) is True


def test_rule_applies_when_section_is_all():
    rule = {"id": "X", "section": "All"}
    assert rule_applies_to_page(rule, [BALANCE_SHEET]) is True
    rule_all_statements = {"id": "Y", "section": "All Statements"}
    assert rule_applies_to_page(rule_all_statements, [STATEMENT_OF_OPERATIONS]) is True
    rule_full_doc = {"id": "Z", "section": "Full Document"}
    assert rule_applies_to_page(rule_full_doc, []) is True


def test_rule_applies_when_unclassified_page_fail_open():
    rule = {"id": "BS-FMT", "section": "Balance Sheet"}
    assert rule_applies_to_page(rule, []) is True


def test_rule_applies_when_page_type_matches():
    rule = {"id": "BS-FMT", "section": "Balance Sheet"}
    assert rule_applies_to_page(rule, [BALANCE_SHEET]) is True
    assert rule_applies_to_page(rule, [BALANCE_SHEET, STATEMENT_OF_OPERATIONS]) is True


def test_rule_skipped_when_page_type_does_not_match():
    rule = {"id": "BS-FMT", "section": "Balance Sheet"}
    assert rule_applies_to_page(rule, [STATEMENT_OF_CASH_FLOWS]) is False


def test_rule_applies_with_alias_section_names():
    rule = {"id": "BS-ALIAS", "section": "Statement of Assets and Liabilities"}
    assert rule_applies_to_page(rule, [BALANCE_SHEET]) is True
    rule_income = {"id": "SOI-ALIAS", "section": "Statement of Income"}
    assert rule_applies_to_page(rule_income, [STATEMENT_OF_OPERATIONS]) is True


def test_rule_applies_when_section_is_unknown_string():
    rule = {"id": "UNK", "section": "Some Weird Section"}
    assert rule_applies_to_page(rule, [BALANCE_SHEET]) is True
