from __future__ import annotations

from fastapi import APIRouter

from src.schemas.rule import RulesResponse
from src.services.rule_service import RuleService


router = APIRouter(prefix="/rules", tags=["rules"])
service = RuleService()


@router.get("", response_model=RulesResponse)
async def list_rules(rules_path: str | None = None) -> RulesResponse:
    return RulesResponse(rules=service.list_rules(rules_json_path=rules_path))
