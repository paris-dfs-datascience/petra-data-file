from __future__ import annotations

from pathlib import Path

from src.providers.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    def __init__(self, root: str, public_base_url: str = "/public") -> None:
        self.root = Path(root)
        self.public_base_url = public_base_url.rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, relative_path: str, content: bytes, content_type: str | None = None) -> str:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def read_bytes(self, relative_path: str) -> bytes:
        return (self.root / relative_path).read_bytes()

    def get_public_url(self, relative_path: str) -> str:
        return f"{self.public_base_url}/{relative_path.lstrip('/')}"
