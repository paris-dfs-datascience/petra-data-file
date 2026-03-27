from __future__ import annotations

from collections.abc import Callable

from src.core.config import Settings
from src.core.prompting import load_prompt
from src.providers.text.openai import OpenAITextAnalysisProvider


TEXT_PROMPT_PATH = "config/text_analysis_system_prompt.md"


def _page_blob(page: dict) -> str:
    text = (page.get("text") or "").strip() or "No text extracted."
    return f"## Page {page.get('page', '?')}\nPlain Extracted Text:\n{text}"


def _serialize_page_content(page: dict) -> str:
    return _page_blob(page)


def _build_skipped_result(rule: dict, message: str, execution_status: str = "skipped", page: int | None = None) -> dict:
    return {
        "page": page,
        "rule_id": rule.get("id", ""),
        "rule_name": rule.get("name", rule.get("id", "")),
        "analysis_type": "text",
        "execution_status": execution_status,
        "verdict": "needs_review",
        "summary": message,
        "reasoning": message,
        "findings": [],
        "citations": [],
        "matched_pages": [],
        "notes": [message],
    }


class TextRuleAnalyzer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.system_prompt = load_prompt(TEXT_PROMPT_PATH)

    def _aggregate_rule_results(self, rule: dict, page_results: list[dict]) -> dict:
        completed_results = [item for item in page_results if item.get("execution_status") == "completed"]
        matched_pages = sorted(
            {
                int(citation.get("page", item.get("page", 0)))
                for item in completed_results
                for citation in item.get("citations", [])
                if int(citation.get("page", item.get("page", 0))) > 0
            }
            | {
                int(item.get("page", 0))
                for item in completed_results
                if item.get("verdict") in {"pass", "fail", "needs_review"} and int(item.get("page", 0)) > 0
            }
        )
        verdict = "needs_review"
        if any(item.get("verdict") == "fail" for item in completed_results):
            verdict = "fail"
        elif completed_results and all(item.get("verdict") in {"pass", "not_applicable"} for item in completed_results):
            verdict = "pass"

        summary_parts = [
            f"Page {item.get('page')}: {item.get('verdict', 'needs_review')}"
            for item in page_results
            if item.get("page") is not None
        ]
        findings: list[str] = []
        citations: list[dict] = []
        notes: list[str] = []
        for item in page_results:
            findings.extend(item.get("findings", [])[:2])
            citations.extend(item.get("citations", [])[:2])
            notes.extend(item.get("notes", [])[:1])

        return {
            "rule_id": rule.get("id", ""),
            "rule_name": rule.get("name", rule.get("id", "")),
            "analysis_type": "text",
            "execution_status": "completed" if completed_results else "error",
            "verdict": verdict,
            "summary": " | ".join(summary_parts[:6]) or "No page-level text analysis result was produced.",
            "reasoning": "Aggregated from page-level text analysis results.",
            "findings": findings[:4],
            "citations": citations[:4],
            "matched_pages": matched_pages,
            "notes": notes[:4],
        }

    def analyze(
        self,
        pages: list[dict],
        rules: list[dict],
        on_page_result: Callable[[dict, dict[str, dict], list[dict]], None] | None = None,
        is_cancelled: Callable[[], bool] | None = None,
    ) -> dict[str, list[dict] | dict[str, dict]]:
        text_rules = [rule for rule in rules if rule.get("analysis_type", "text") == "text"]
        if not text_rules:
            return {"rule_results": {}, "page_results": []}

        if not self.settings.OPENAI_API_KEY:
            return {
                "rule_results": {
                    rule.get("id", ""): _build_skipped_result(
                        rule,
                        "OpenAI API key is not configured. Text analysis was skipped.",
                    )
                    for rule in text_rules
                },
                "page_results": [],
            }

        provider = OpenAITextAnalysisProvider(
            api_key=self.settings.OPENAI_API_KEY,
            model_id=self.settings.OPENAI_TEXT_MODEL,
            temperature=self.settings.OPENAI_TEXT_TEMPERATURE,
            max_completion_tokens=self.settings.OPENAI_TEXT_MAX_COMPLETION_TOKENS,
        )
        results: dict[str, dict] = {}
        page_results: list[dict] = []
        for rule in text_rules:
            rule_id = rule.get("id", "")
            per_rule_page_results: list[dict] = []
            for page in pages:
                if is_cancelled and is_cancelled():
                    results[rule_id] = self._aggregate_rule_results(rule, per_rule_page_results)
                    return {"rule_results": results, "page_results": page_results}
                page_number = int(page.get("page", 0))
                try:
                    document_content = _serialize_page_content(page)
                    raw_result = provider.evaluate_rule(document_content=document_content, rule=rule, system_prompt=self.system_prompt)
                    citations = raw_result.get("citations", [])
                    normalized_citations = [
                        {
                            "page": int(item.get("page", page_number) or page_number),
                            "evidence": item.get("evidence", ""),
                        }
                        for item in citations
                    ]
                    page_result = {
                        "page": page_number,
                        "rule_id": raw_result.get("rule_id", rule_id),
                        "rule_name": raw_result.get("rule_name", rule.get("name", rule_id)),
                        "analysis_type": "text",
                        "execution_status": "completed",
                        "verdict": raw_result.get("verdict", "needs_review"),
                        "summary": raw_result.get("summary", ""),
                        "reasoning": raw_result.get("reasoning", ""),
                        "findings": raw_result.get("findings", []),
                        "citations": normalized_citations,
                        "notes": [f"Confidence: {raw_result.get('confidence', 'unknown')}"],
                    }
                except Exception as exc:
                    page_result = _build_skipped_result(
                        rule,
                        f"Text analysis failed: {exc}",
                        execution_status="error",
                        page=page_number,
                    )
                per_rule_page_results.append(page_result)
                page_results.append(page_result)
                results[rule_id] = self._aggregate_rule_results(rule, per_rule_page_results)
                if on_page_result:
                    on_page_result(page_result, dict(results), list(page_results))
            results[rule_id] = self._aggregate_rule_results(rule, per_rule_page_results)
        return {"rule_results": results, "page_results": page_results}
