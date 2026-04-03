from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalysisCitation(BaseModel):
    page: int
    evidence: str = ""


class AnalysisRuleResult(BaseModel):
    rule_id: str
    rule_name: str
    verdict: Literal["pass", "fail", "needs_review", "not_applicable"]
    summary: str
    reasoning: str
    findings: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]
    citations: list[AnalysisCitation] = Field(default_factory=list)


RULE_RESULT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "rule_id": {"type": "string"},
        "rule_name": {"type": "string"},
        "verdict": {"type": "string", "enum": ["pass", "fail", "needs_review", "not_applicable"]},
        "summary": {"type": "string"},
        "reasoning": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {"type": "string"},
        },
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "evidence": {"type": "string"},
                },
                "required": ["page", "evidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["rule_id", "rule_name", "verdict", "summary", "reasoning", "findings", "confidence", "citations"],
    "additionalProperties": False,
}


def compact_rule_payload(rule: dict, fallback_analysis_type: str) -> str:
    return (
        f"RULE ID: {rule.get('id', '')}\n"
        f"RULE NAME: {rule.get('name', '')}\n"
        f"RULE TYPE: {rule.get('analysis_type', fallback_analysis_type)}\n"
        f"RULE QUERY: {rule.get('query', '')}\n"
        f"RULE DESCRIPTION: {rule.get('description', '')}\n"
        f"RULE ACCEPTANCE CRITERIA: {rule.get('acceptance_criteria', '')}\n"
    )
