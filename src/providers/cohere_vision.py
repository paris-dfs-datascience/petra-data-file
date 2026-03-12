from __future__ import annotations

import json
from typing import Any, Dict, List

import cohere


RULE_RESULT_JSON_SCHEMA: dict = {
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
    "required": [
        "rule_id",
        "rule_name",
        "status",
        "reasoning",
        "citations",
    ],
    "additionalProperties": False,
}


class CohereVisionValidator:
    def __init__(
        self,
        api_key: str,
        model_id: str = "command-a-vision-07-2025",
        temperature: float = 0.1,
        seed: int = 42,
        max_tokens: int = 1200,
        image_detail: str = "high",
    ) -> None:
        self._co = cohere.ClientV2(api_key=api_key)
        self._model = model_id
        self._temperature = temperature
        self._seed = seed
        self._max_tokens = max_tokens
        self._detail = image_detail

    def evaluate_rule(
        self,
        images_data_urls: list[str],
        rule: dict,
        system_prompt: str,
    ) -> Dict[str, Any]:
        """Call Command A Vision with images + rule and force JSON schema output."""
        # Build content list
        content = [
            {
                "type": "text",
                "text": (
                    "Evaluate the following RULE against the provided pages of a financial statement. "
                    "Return JSON ONLY, matching the schema. Do not include any extra text.\n\n"
                    f"RULE JSON:\n{json.dumps(rule, ensure_ascii=False)}\n\n"
                    "Instructions:\n"
                    "- Use only the provided images.\n"
                    "- If evidence is unclear, choose 'fail' and explain.\n"
                    "- Provide citations as page numbers you used (1-based), "
                    "and (optionally) short snippets or headings.\n"
                ),
            }
        ]
        for url in images_data_urls:
            content.append({"type": "image_url", "image_url": {"url": url, "detail": self._detail}})

        messages = [{"role": "user", "content": content}]
        if system_prompt and system_prompt.strip():
            messages.insert(0, {"role": "system", "content": system_prompt})

        res = self._co.chat(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
            seed=self._seed,
            max_tokens=self._max_tokens,
            response_format={
                "type": "json_object",
                "schema": RULE_RESULT_JSON_SCHEMA,
            },
        )
        # Cohere v2 returns message.content as a list of content parts
        text = res.message.content[0].text
        try:
            data = json.loads(text)
        except Exception as e:
            # Fallback: wrap raw text if parsing fails
            data = {
                "rule_id": rule.get("id", ""),
                "rule_name": rule.get("name", ""),
                "status": "fail",
                "reasoning": f"Model did not return valid JSON: {e}. Raw: {text[:2000]}",
                "citations": [],
            }
        return data
