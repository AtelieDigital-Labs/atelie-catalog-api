from boto3 import client
from botocore.client import BaseClient
from fastapi import Depends
from typing import Annotated
from .config import settings


def get_storage() -> BaseClient:
    
    return client(
        's3',
        endpoint_url=settings.MINIO_ENDPOINT_URL,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name='us-east-1',
    )


S3Client = Annotated[BaseClient, Depends(get_storage)]
