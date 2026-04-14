from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class RuleSchema(BaseModel):
    id: str
    name: str
    analysis_type: Literal["text", "vision"] = "text"
    query: str
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    severity: Optional[str] = None
    group: Optional[str] = None
    section: Optional[str] = None
    bypassable: bool = False
    bypass: bool = False  # runtime: user opted to bypass this rule for this run
    tolerance: Optional[float] = None
    check_method: Optional[str] = None
    steps: Optional[str] = None
    pass_criteria: Optional[str] = None
    fail_criteria: Optional[str] = None
    action_if_fail: Optional[str] = None
    rationale: Optional[str] = None


class RulesResponse(BaseModel):
    rules: list[RuleSchema]
