from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TextAnalysisProvider(ABC):
    @abstractmethod
    def evaluate_rule(self, document_content: str, rule: dict, system_prompt: str) -> dict[str, Any]:
        raise NotImplementedError
