from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VisionProvider(ABC):
    @abstractmethod
    def evaluate_rule(self, page_image: dict[str, Any], rule: dict, system_prompt: str) -> dict[str, Any]:
        raise NotImplementedError
