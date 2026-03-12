from __future__ import annotations

import json
from typing import Any, Dict, List
import threading

from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Global semaphore to limit concurrent OpenAI requests across all users
_GLOBAL_OPENAI_SEMAPHORE = None
_SEMAPHORE_LOCK = threading.Lock()


def get_global_semaphore(max_concurrent: int = 10) -> threading.Semaphore:
    """Get or create the global OpenAI rate limiting semaphore."""
    global _GLOBAL_OPENAI_SEMAPHORE
    with _SEMAPHORE_LOCK:
        if _GLOBAL_OPENAI_SEMAPHORE is None:
            _GLOBAL_OPENAI_SEMAPHORE = threading.Semaphore(max_concurrent)
    return _GLOBAL_OPENAI_SEMAPHORE


# Shared JSON schema for rule validation results
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

# Schema for evaluating multiple rules at once
RULES_BATCH_RESULT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": RULE_RESULT_JSON_SCHEMA,
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


class OpenAIVisionValidator:
    """OpenAI vision validator using GPT-4o or GPT-5 with structured outputs."""

    def __init__(
        self,
        api_key: str,
        model_id: str = "gpt-4o",
        temperature: float = 0.1,
        seed: int | None = None,
        max_completion_tokens: int = 1200,  # Updated parameter name
        image_detail: str = "high",
        max_concurrent: int = 10,
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
    def _call_openai_with_retry(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        schema_name: str,
    ) -> str:
        """Call OpenAI API with retry logic and rate limiting."""
        with self._semaphore:
            # Use max_completion_tokens if using o1/o3 or if you prefer it for gpt-4o
            # For older compatibility you might check model name, but newer SDKs allow it.
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=self._temperature,
                seed=self._seed,
                max_completion_tokens=self._max_tokens,  # Updated parameter
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "strict": True,
                        "schema": schema
                    }
                }
            )
            return response.choices[0].message.content

    def evaluate_rule(
        self,
        images_data_urls: list[str],
        rule: dict,
        system_prompt: str,
    ) -> Dict[str, Any]:
        """Call OpenAI vision model with images + rule and force JSON schema output."""
        # Build content list with singular/plural phrasing based on image count
        pages_word = "page" if len(images_data_urls) == 1 else "pages"
        content = [
            {
                "type": "text",
                "text": (
                    f"Evaluate the following RULE against the provided {pages_word} of a financial statement. "
                    "Return JSON ONLY, matching the schema. Do not include any extra text.\n\n"
                    f"RULE JSON:\n{json.dumps(rule, ensure_ascii=False)}\n\n"
                    "Instructions:\n"
                    "- Use only the provided images.\n"
                    "- If evidence is unclear, choose fail and explain.\n"
                    "- Provide citations as page numbers you used (1-based), "
                    "and (optionally) short snippets or headings.\n"
                ),
            }
        ]
        
        # Add images
        for url in images_data_urls:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": url,
                    "detail": self._detail
                }
            })

        # Build messages
        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        # Call OpenAI with structured outputs (JSON mode) with retry
        try:
            text = self._call_openai_with_retry(
                messages=messages,
                schema=RULE_RESULT_JSON_SCHEMA,
                schema_name="rule_result",
            )
            data = json.loads(text)
            
        except Exception as e:
            # Fallback: wrap error in valid schema
            data = {
                "rule_id": rule.get("id", ""),
                "rule_name": rule.get("name", ""),
                "status": "fail",
                "reasoning": f"OpenAI API error: {str(e)}",
                "citations": [],
            }
        
        return data

    def evaluate_rules(
        self,
        image_data_url: str,
        rules: list[dict],
        system_prompt: str,
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple rules against a single page image in one API call."""
        # Build content with all rules at once
        rules_json = json.dumps(rules, ensure_ascii=False, indent=2)
        content = [
            {
                "type": "text",
                "text": (
                    f"Evaluate ALL of the following RULES against the provided page image. "
                    "Return a JSON array with one result object per rule, matching the schema. "
                    "Do not include any extra text.\n\n"
                    f"RULES JSON:\n{rules_json}\n\n"
                    "Instructions:\n"
                    "- For each rule, decide if the page passes or fails.\n"
                    "- Use only the provided image.\n"
                    "- If evidence is unclear for a rule, choose 'fail' and explain.\n"
                    "- Provide citations as page numbers (1-based) and optionally short snippets.\n"
                    "- Return results in the same order as the input rules.\n"
                ),
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data_url,
                    "detail": self._detail
                }
            }
        ]

        # Build messages
        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        # Call OpenAI with structured outputs (batch schema) with retry
        try:
            text = self._call_openai_with_retry(
                messages=messages,
                schema=RULES_BATCH_RESULT_SCHEMA,
                schema_name="rules_batch_result",
            )
            data = json.loads(text)
            results = data.get("results", [])
            
        except Exception as e:
            # Fallback: create error results for all rules
            results = []
            for rule in rules:
                results.append({
                    "rule_id": rule.get("id", ""),
                    "rule_name": rule.get("name", ""),
                    "status": "fail",
                    "reasoning": f"OpenAI API error: {str(e)}",
                    "citations": [],
                })
        
        return results
