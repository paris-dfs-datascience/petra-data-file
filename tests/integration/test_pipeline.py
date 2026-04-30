"""Integration tests for the end-to-end validation pipeline.

Each test node corresponds to one (case, rule) pair defined in cases.yaml.
The session-scoped `pipeline_results` fixture (conftest.py) runs the real
validation pipeline — including live LLM calls — once per case and caches
the result so every rule assertion for the same document shares a single run.

Running:
    pytest tests/integration -m integration           # all cases
    pytest tests/integration -m integration -k foo    # filter by name
    pytest tests/integration -m integration -v        # verbose

Adding cases: see the instructions at the top of cases.yaml, or run
    python scripts/update_integration_expectations.py
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_CASES_FILE = Path(__file__).parent / "cases.yaml"


def _collect_params() -> list[pytest.param]:
    data = yaml.safe_load(_CASES_FILE.read_text())
    cases = (data or {}).get("cases") or []
    params: list[pytest.param] = []
    for case in cases:
        for exp in case.get("expected") or []:
            pages_filter = exp.get("pages")
            pages_suffix = (
                f"[p{','.join(str(p) for p in sorted(pages_filter))}]"
                if pages_filter
                else ""
            )
            node_id = f"{case['id']}/{exp['rule_id']}{pages_suffix}"
            params.append(
                pytest.param(
                    case["id"],
                    exp["rule_id"],
                    exp["verdict"],
                    exp.get("matched_pages"),
                    pages_filter,
                    id=node_id,
                )
            )
    return params


_PARAMS = _collect_params()


def _reaggregate_verdict(page_results: list[dict], rule_id: str, pages: list[int]) -> str:
    """Re-aggregate a verdict from page-level results restricted to the given pages."""
    pages_set = set(pages)
    filtered = [
        r
        for r in page_results
        if r.get("rule_id") == rule_id
        and int(r.get("page", 0)) in pages_set
        and r.get("execution_status") == "completed"
    ]
    if not filtered:
        return "needs_review"
    if any(r.get("verdict") == "fail" for r in filtered):
        return "fail"
    if all(r.get("verdict") in {"pass", "not_applicable"} for r in filtered):
        return "pass"
    return "needs_review"


@pytest.mark.integration
@pytest.mark.parametrize(
    "case_id,rule_id,expected_verdict,expected_pages,pages_filter",
    _PARAMS if _PARAMS else [pytest.param("_none", "_none", "_none", None, None, id="no_cases")],
)
def test_rule_verdict(
    pipeline_results: dict,
    case_id: str,
    rule_id: str,
    expected_verdict: str,
    expected_pages: list[int] | None,
    pages_filter: list[int] | None,
) -> None:
    if case_id == "_none":
        pytest.skip("No integration test cases defined in cases.yaml")

    result = pipeline_results.get(case_id)
    if result is None:
        pytest.fail(f"No pipeline result for case '{case_id}' — check conftest.py")

    error = result.get("__error__")
    if error:
        pytest.fail(error)

    assessments: dict[str, dict] = {
        a["rule_id"]: a
        for a in result.get("analysis", {}).get("rule_assessments", [])
    }

    assert rule_id in assessments, (
        f"Rule '{rule_id}' not found in results for case '{case_id}'. "
        f"Rules present: {sorted(assessments)}"
    )

    actual = assessments[rule_id]

    if pages_filter is not None:
        text_page_results = result.get("analysis", {}).get("text_page_results", [])
        visual_page_results = result.get("analysis", {}).get("visual_page_results", [])
        actual_verdict = _reaggregate_verdict(
            text_page_results + visual_page_results, rule_id, pages_filter
        )
        assert actual_verdict == expected_verdict, (
            f"Case '{case_id}' / Rule '{rule_id}' / Pages {sorted(pages_filter)}: "
            f"expected verdict '{expected_verdict}', got '{actual_verdict}'\n"
            f"Findings: {actual.get('findings', [])}"
        )
    else:
        assert actual["verdict"] == expected_verdict, (
            f"Case '{case_id}' / Rule '{rule_id}': "
            f"expected verdict '{expected_verdict}', got '{actual['verdict']}'\n"
            f"Summary: {actual.get('summary', '')}\n"
            f"Findings: {actual.get('findings', [])}"
        )

    if expected_pages is not None:
        assert sorted(actual.get("matched_pages") or []) == sorted(expected_pages), (
            f"Case '{case_id}' / Rule '{rule_id}': "
            f"expected matched_pages {sorted(expected_pages)}, "
            f"got {sorted(actual.get('matched_pages') or [])}"
        )
