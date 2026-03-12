from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from operator import add
from pathlib import Path
from typing import Annotated, Dict, List, TypedDict
import concurrent.futures

from langgraph.graph import StateGraph, START, END

from src.config import load_app_yaml, project_paths, Settings
from src.pdf_utils import pdf_to_images
from src.utils import image_path_to_base64_data_url, image_path_to_base64_data_url_with_centerline, ensure_dir
from src.providers.openai_vision import OpenAIVisionValidator
from src.schemas import Rule, RuleResult, DocumentResult, PageResult


class State(TypedDict, total=False):
    pdf_path: str
    doc_id: str
    image_paths: list[str]
    rules: list[dict]
    pages: list[dict]


def _timestamp_id() -> str:
    return time.strftime("%Y%m%dT%H%M%S")


# === Nodes ===

def node_pdf_to_images(state: State) -> State:
    app = load_app_yaml()
    paths = project_paths(app)
    doc_id = Path(state["pdf_path"]).stem + f"_{_timestamp_id()}"
    out_dir = paths["uploads"] / doc_id / "pages"
    ensure_dir(str(out_dir))
    imgs = pdf_to_images(
        state["pdf_path"],
        str(out_dir),
        dpi=app.pdf.dpi,
        image_format=app.pdf.image_format,
    )
    return {
        **state,
        "doc_id": doc_id,
        "image_paths": imgs,
    }




def node_validate_rules(state: State) -> State:
    """Validate all rules against all pages (one request per rule per page)."""
    app = load_app_yaml()
    s = Settings()

    # Vision provider (OpenAI only now)
    validator = OpenAIVisionValidator(
        api_key=s.OPENAI_API_KEY or "",
        model_id=app.vision.model_id,
        temperature=app.vision.temperature,
        seed=app.vision.seed,
        max_completion_tokens=app.vision.max_completion_tokens,
        image_detail=app.vision.image_detail,
        max_concurrent=app.vision.global_max_concurrent,
    )

    system_prompt = Path("config/system_prompt.md").read_text()

    # Rule ID that requires the centerline overlay
    CENTERLINE_RULE_ID = "FMT-HEADINGS"

    # Helper function to evaluate a single rule on a single page
    def evaluate_single_rule_on_page(
        page_num: int,
        image_url: str,
        image_url_centerline: str,
        rule: dict,
        validator_obj,
        sys_prompt: str,
    ) -> dict:
        """Evaluate one rule on one page (one API call).
        
        For FMT-HEADINGS rule, uses the centerline overlay image; otherwise uses original.
        """
        # Use centerline image only for the FMT-HEADINGS rule
        use_centerline = rule.get("id") == CENTERLINE_RULE_ID
        image_for_llm = image_url_centerline if use_centerline else image_url
        
        try:
            result = validator_obj.evaluate_rule(
                images_data_urls=[image_for_llm],
                rule=rule,
                system_prompt=sys_prompt,
            )
            # Ensure required fields
            result.setdefault("rule_id", rule.get("id", ""))
            result.setdefault("rule_name", rule.get("name", ""))
            # preview_images points to the exact image the LLM saw
            result["preview_images"] = [{"page": page_num, "image_data_url": image_for_llm}]
            return result
        except Exception as e:
            return {
                "rule_id": rule.get("id", ""),
                "rule_name": rule.get("name", ""),
                "status": "fail",
                "reasoning": f"Validation error: {str(e)}",
                "citations": [],
                "preview_images": [{"page": page_num, "image_data_url": image_for_llm}],
            }

    # Process pages with concurrent rule evaluations
    page_results: list[dict] = []
    max_workers = app.vision.concurrent_requests
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, img_path in enumerate(state["image_paths"]):
            page_num = idx + 1  # 1-based
            # Compute both URLs once per page (avoid extra work)
            image_url = image_path_to_base64_data_url(img_path)
            image_url_centerline = image_path_to_base64_data_url_with_centerline(img_path)
            
            # Submit all rules for this page (concurrent per page)
            rule_futures = []
            for rule in state["rules"]:
                future = executor.submit(
                    evaluate_single_rule_on_page,
                    page_num,
                    image_url,
                    image_url_centerline,
                    rule,
                    validator,
                    system_prompt,
                )
                rule_futures.append((rule.get("id", ""), future))
            
            # Collect results for this page
            rule_results = []
            for rule_id, future in rule_futures:
                try:
                    result = future.result()
                    rule_results.append(result)
                except Exception as e:
                    # Fallback error result for this rule
                    rule_results.append({
                        "rule_id": rule_id,
                        "rule_name": "",
                        "status": "fail",
                        "reasoning": f"Processing error: {str(e)}",
                        "citations": [],
                        "preview_images": [{"page": page_num, "image_data_url": image_url}],
                    })
            
            # Sort rule results by rule_id to maintain consistent order
            rule_results.sort(key=lambda r: r.get("rule_id", ""))
            
            # Create page result with both original and centerline URLs
            page_results.append({
                "page": page_num,
                "image_data_url": image_url,
                "image_data_url_centerline": image_url_centerline,
                "rules": rule_results,
            })
    
    return {**state, "pages": page_results}


def build_graph():
    """Build the simplified pipeline: PDF -> Images -> Validate."""
    graph = StateGraph(State)
    graph.add_node("pdf_to_images", node_pdf_to_images)
    graph.add_node("validate_rules", node_validate_rules)

    graph.add_edge(START, "pdf_to_images")
    graph.add_edge("pdf_to_images", "validate_rules")
    graph.add_edge("validate_rules", END)
    return graph.compile()
