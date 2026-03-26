from __future__ import annotations

from src.core.config import Settings
from src.providers.storage.base import StorageProvider
from src.providers.storage.local import LocalStorageProvider


def get_storage_provider(settings: Settings) -> StorageProvider:
    backend = settings.STORAGE_BACKEND.lower()

    if backend == "azure_blob":
        from src.providers.storage.azure_blob import AzureBlobStorageProvider

        if not settings.AZURE_BLOB_CONNECTION_STRING or not settings.AZURE_BLOB_CONTAINER:
            raise ValueError("Azure Blob storage requires AZURE_BLOB_CONNECTION_STRING and AZURE_BLOB_CONTAINER.")
        return AzureBlobStorageProvider(
            connection_string=settings.AZURE_BLOB_CONNECTION_STRING,
            container=settings.AZURE_BLOB_CONTAINER,
        )

    if backend in {"s3", "minio"}:
        from src.providers.storage.s3 import S3StorageProvider

        if not settings.S3_BUCKET:
            raise ValueError("S3-compatible storage requires S3_BUCKET.")
        return S3StorageProvider(
            bucket=settings.S3_BUCKET,
            region=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key_id=settings.S3_ACCESS_KEY_ID,
            secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        )

    return LocalStorageProvider(root=settings.PUBLIC_DIR)
