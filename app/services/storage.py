from pathlib import Path
from uuid import uuid4

from boto3 import client
from botocore.client import BaseClient
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import settings
from urllib.parse import urlparse, urlunparse


class StorageService:
    _client: BaseClient = client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT_URL,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1",
    )

    _bucket = settings.MINIO_BUCKET

    @staticmethod
    def ensure_bucket() -> None:
        try:
            StorageService._client.head_bucket(
                Bucket=StorageService._bucket,
            )
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]

            if error_code in ("404", "NoSuchBucket"):
                StorageService._client.create_bucket(
                    Bucket=StorageService._bucket,
                )
            else:
                raise

    @staticmethod
    def upload(
        file: UploadFile,
        directory: str,
    ) -> str:
        key = f"{directory}/{uuid4()}{Path(file.filename).suffix}"

        StorageService._client.upload_fileobj(
            file.file,
            StorageService._bucket,
            key,
            ExtraArgs={
                "ContentType": file.content_type,
            },
        )

        return key

    @staticmethod
    def delete(key: str) -> None:
        StorageService._client.delete_object(
            Bucket=StorageService._bucket,
            Key=key,
        )

    @staticmethod
    def exists(key: str) -> bool:
        try:
            StorageService._client.head_object(
                Bucket=StorageService._bucket,
                Key=key,
            )
            return True
        except ClientError:
            return False

    @staticmethod
    def public_url(key: str) -> str:
        return (
            f"{settings.MINIO_PUBLIC_URL}/"
            f"{StorageService._bucket}/"
            f"{key}"
        )

    @staticmethod
    def presigned_url(key: str, expires_in: int = 300) -> str:
        url = StorageService._client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": StorageService._bucket,
                "Key": key,
            },
            ExpiresIn=expires_in,
        )

        internal = urlparse(settings.MINIO_ENDPOINT_URL)
        public = urlparse(settings.MINIO_PUBLIC_URL)

        parsed = urlparse(url)

        return urlunparse(
            parsed._replace(
                scheme=public.scheme,
                netloc=public.netloc,
            )
        )

    @staticmethod
    def download(key: str) -> bytes:
        response = StorageService._client.get_object(
            Bucket=StorageService._bucket,
            Key=key,
        )

        return response["Body"].read()