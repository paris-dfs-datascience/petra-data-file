from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class RuleSchema(BaseModel):
    id: str
    name: str
    query: str
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    severity: Optional[str] = None


class RulesResponse(BaseModel):
    rules: list[RuleSchema]
