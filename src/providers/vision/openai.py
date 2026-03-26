from __future__ import annotations

import json
import threading
from typing import Any

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.providers.vision.base import VisionProvider


_GLOBAL_OPENAI_SEMAPHORE = None
_SEMAPHORE_LOCK = threading.Lock()


def get_global_semaphore(max_concurrent: int = 10) -> threading.Semaphore:
    global _GLOBAL_OPENAI_SEMAPHORE
    with _SEMAPHORE_LOCK:
        if _GLOBAL_OPENAI_SEMAPHORE is None:
            _GLOBAL_OPENAI_SEMAPHORE = threading.Semaphore(max_concurrent)
    return _GLOBAL_OPENAI_SEMAPHORE


RULE_RESULT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "rule_id": {"type": "string"},
        "rule_name": {"type": "string"},
        "status": {"type": "string", "enum": ["pass", "fail"]},
        "reasoning": {"type": "string"},
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
    "required": ["rule_id", "rule_name", "status", "reasoning", "citations"],
    "additionalProperties": False,
}


class OpenAIVisionProvider(VisionProvider):
    def __init__(
        self,
        api_key: str,
        model_id: str,
        temperature: float,
        seed: int | None,
        max_completion_tokens: int,
        image_detail: str,
        max_concurrent: int,
    ) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model_id
        self._temperature = temperature
        self._seed = seed
        self._max_tokens = max_completion_tokens
        self._detail = image_detail
        self._semaphore = get_global_semaphore(max_concurrent)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def _call_openai_with_retry(self, messages: list[dict[str, Any]], schema: dict[str, Any], schema_name: str) -> str:
        with self._semaphore:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=self._temperature,
                seed=self._seed,
                max_completion_tokens=self._max_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "strict": True,
                        "schema": schema,
                    },
                },
            )
        return response.choices[0].message.content

    def evaluate_rule(self, images_data_urls: list[str], rule: dict, system_prompt: str) -> dict[str, Any]:
        pages_word = "page" if len(images_data_urls) == 1 else "pages"
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    f"Evaluate the following RULE against the provided {pages_word} of a financial statement. "
                    "Return JSON ONLY, matching the schema. Do not include any extra text.\n\n"
                    f"RULE JSON:\n{json.dumps(rule, ensure_ascii=False)}\n\n"
                    "Instructions:\n"
                    "- Use only the provided images.\n"
                    "- If evidence is unclear, choose fail and explain.\n"
                    "- Provide citations as page numbers you used (1-based), and optionally short snippets or headings.\n"
                ),
            }
        ]
        for url in images_data_urls:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": url, "detail": self._detail},
                }
            )

        messages: list[dict[str, Any]] = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        try:
            text = self._call_openai_with_retry(messages, RULE_RESULT_JSON_SCHEMA, "rule_result")
            return json.loads(text)
        except Exception as exc:
            return {
                "rule_id": rule.get("id", ""),
                "rule_name": rule.get("name", ""),
                "status": "fail",
                "reasoning": f"OpenAI API error: {exc}",
                "citations": [],
            }
