from __future__ import annotations

import boto3

from src.providers.storage.base import StorageProvider


class S3StorageProvider(StorageProvider):
    def __init__(
        self,
        bucket: str,
        region: str | None = None,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def save_bytes(self, relative_path: str, content: bytes, content_type: str | None = None) -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=relative_path,
            Body=content,
            ContentType=content_type or "application/octet-stream",
        )
        return f"s3://{self.bucket}/{relative_path}"

    def read_bytes(self, relative_path: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=relative_path)
        return obj["Body"].read()
