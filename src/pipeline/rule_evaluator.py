from __future__ import annotations

import concurrent.futures
from pathlib import Path

from src.pipeline.result_builder import image_path_to_base64_data_url, image_path_to_base64_data_url_with_centerline
from src.providers.vision.base import VisionProvider


class RuleEvaluator:
    CENTERLINE_RULE_ID = "FMT-HEADINGS"

    def __init__(self, provider: VisionProvider, concurrent_requests: int) -> None:
        self.provider = provider
        self.concurrent_requests = concurrent_requests

    def evaluate_pages(self, image_paths: list[str], rules: list[dict], system_prompt_path: str) -> list[dict]:
        system_prompt = Path(system_prompt_path).read_text(encoding="utf-8")
        page_results: list[dict] = []

        def evaluate_single_rule(page_num: int, image_url: str, image_url_centerline: str, rule: dict) -> dict:
            use_centerline = rule.get("id") == self.CENTERLINE_RULE_ID
            llm_image = image_url_centerline if use_centerline else image_url
            try:
                result = self.provider.evaluate_rule([llm_image], rule, system_prompt)
                result.setdefault("rule_id", rule.get("id", ""))
                result.setdefault("rule_name", rule.get("name", ""))
                result["preview_images"] = [{"page": page_num, "image_data_url": llm_image}]
                return result
            except Exception as exc:
                return {
                    "rule_id": rule.get("id", ""),
                    "rule_name": rule.get("name", ""),
                    "status": "fail",
                    "reasoning": f"Validation error: {exc}",
                    "citations": [],
                    "preview_images": [{"page": page_num, "image_data_url": llm_image}],
                }

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent_requests) as executor:
            for idx, image_path in enumerate(image_paths):
                page_num = idx + 1
                image_url = image_path_to_base64_data_url(image_path)
                image_url_centerline = image_path_to_base64_data_url_with_centerline(image_path)

                futures = [
                    executor.submit(evaluate_single_rule, page_num, image_url, image_url_centerline, rule)
                    for rule in rules
                ]
                rule_results = [future.result() for future in futures]
                rule_results.sort(key=lambda item: item.get("rule_id", ""))
                page_results.append(
                    {
                        "page": page_num,
                        "image_data_url": image_url,
                        "image_data_url_centerline": image_url_centerline,
                        "rules": rule_results,
                    }
                )

        return page_results
