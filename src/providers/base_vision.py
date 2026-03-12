from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class VisionValidator(ABC):
    @abstractmethod
    def evaluate_rule(
        self,
        images_data_urls: list[str],
        rule: dict,
        system_prompt: str,
    ) -> Dict[str, Any]:
        """Return a structured dict complying with the shared JSON schema."""
        ...
