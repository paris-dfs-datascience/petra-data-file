from __future__ import annotations

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    @abstractmethod
    def save_bytes(self, relative_path: str, content: bytes, content_type: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def read_bytes(self, relative_path: str) -> bytes:
        raise NotImplementedError

    def get_public_url(self, relative_path: str) -> str | None:
        return None
