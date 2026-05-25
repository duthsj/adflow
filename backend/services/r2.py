import uuid
import boto3
from botocore.client import Config
from ..config import settings

def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint,
        aws_access_key_id=settings.r2_access_key,
        aws_secret_access_key=settings.r2_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

def r2_upload(file_bytes: bytes, filename: str, content_type: str) -> str:
    key = f"assets/{uuid.uuid4()}/{filename}"
    _client().put_object(
        Bucket=settings.r2_bucket,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return key

def r2_presigned_url(key: str, expires: int = 3600) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.r2_bucket, "Key": key},
        ExpiresIn=expires,
    )

def r2_delete(key: str) -> None:
    _client().delete_object(Bucket=settings.r2_bucket, Key=key)
