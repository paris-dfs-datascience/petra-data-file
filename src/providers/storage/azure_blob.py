from __future__ import annotations

from azure.storage.blob import BlobServiceClient

from src.providers.storage.base import StorageProvider


class AzureBlobStorageProvider(StorageProvider):
    def __init__(self, connection_string: str, container: str) -> None:
        self.container = container
        self.client = BlobServiceClient.from_connection_string(connection_string)

    def save_bytes(self, relative_path: str, content: bytes, content_type: str | None = None) -> str:
        blob_client = self.client.get_blob_client(container=self.container, blob=relative_path)
        blob_client.upload_blob(content, overwrite=True)
        return f"azure://{self.container}/{relative_path}"

    def read_bytes(self, relative_path: str) -> bytes:
        blob_client = self.client.get_blob_client(container=self.container, blob=relative_path)
        return blob_client.download_blob().readall()
