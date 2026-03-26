from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.rule import Rule


class RuleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active(self) -> list[Rule]:
        return list(self.db.scalars(select(Rule).where(Rule.is_active.is_(True))).all())
