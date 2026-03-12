from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
import numpy as np


class EmbeddingsProvider(ABC):
    @abstractmethod
    def embed_images(self, image_paths: list[str]) -> np.ndarray:
        ...

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> np.ndarray:
        ...

    @property
    @abstractmethod
    def dim(self) -> int:
        ...
