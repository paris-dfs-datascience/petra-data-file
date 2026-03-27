from __future__ import annotations

import json
from pathlib import Path

from src.schemas.rule import RuleSchema


class RuleService:
    def load_rules(self, rules_json_path: str | None = None, rules_json_str: str | None = None) -> list[dict]:
        rules_data: list[dict]
        if rules_json_str:
            rules_data = json.loads(rules_json_str)["rules"]
        else:
            path = rules_json_path or "rules/rules.json"
            rules_data = json.loads(Path(path).read_text(encoding="utf-8"))["rules"]
        for rule in rules_data:
            rule.setdefault("analysis_type", "text")
        return rules_data

    def list_rules(self, rules_json_path: str | None = None) -> list[RuleSchema]:
        return [RuleSchema(**rule) for rule in self.load_rules(rules_json_path=rules_json_path)]
