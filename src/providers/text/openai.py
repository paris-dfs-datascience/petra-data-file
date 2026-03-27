from __future__ import annotations

from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.providers.text.base import TextAnalysisProvider


class TextRuleCitation(BaseModel):
    page: int
    evidence: str = ""


class TextRuleResult(BaseModel):
    rule_id: str
    rule_name: str
    verdict: str
    summary: str
    reasoning: str
    findings: list[str] = Field(default_factory=list)
    confidence: str
    citations: list[TextRuleCitation] = Field(default_factory=list)


def _compact_rule_payload(rule: dict) -> str:
    return (
        f"RULE ID: {rule.get('id', '')}\n"
        f"RULE NAME: {rule.get('name', '')}\n"
        f"RULE TYPE: {rule.get('analysis_type', 'text')}\n"
        f"RULE QUERY: {rule.get('query', '')}\n"
        f"RULE DESCRIPTION: {rule.get('description', '')}\n"
        f"RULE ACCEPTANCE CRITERIA: {rule.get('acceptance_criteria', '')}\n"
    )


class OpenAITextAnalysisProvider(TextAnalysisProvider):
    def __init__(
        self,
        api_key: str,
        model_id: str,
        temperature: float | None,
        max_completion_tokens: int | None,
    ) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model_id
        self._temperature = temperature
        self._max_tokens = max_completion_tokens

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def _call_openai_with_retry(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        request_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "response_format": TextRuleResult,
        }
        if self._max_tokens is not None:
            request_kwargs["max_completion_tokens"] = self._max_tokens
        if self._temperature is not None:
            request_kwargs["temperature"] = self._temperature

        response = self._client.beta.chat.completions.parse(
            **request_kwargs,
        )
        message = response.choices[0].message
        if message.parsed is not None:
            return message.parsed.model_dump()
        if message.refusal:
            raise ValueError(f"Model refused to answer: {message.refusal}")
        content = message.content or ""
        raise ValueError(f"Model returned no structured content. Raw content: {content!r}")

    def evaluate_rule(self, document_content: str, rule: dict, system_prompt: str) -> dict[str, Any]:
        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append(
            {
                "role": "user",
                "content": (
                    "Evaluate the following text/content rule against the extracted PDF content.\n"
                    "Be concise.\n\n"
                    f"{_compact_rule_payload(rule)}\n"
                    "EXTRACTED DOCUMENT CONTENT:\n"
                    f"{document_content}\n"
                ),
            }
        )
        return self._call_openai_with_retry(messages)
