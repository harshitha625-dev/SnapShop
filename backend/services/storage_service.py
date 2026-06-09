import boto3, hashlib
from botocore.exceptions import ClientError
from backend.config import settings

s3 = boto3.client(
    "s3",
    endpoint_url=         settings.R2_ENDPOINT_URL,
    aws_access_key_id=    settings.R2_ACCESS_KEY,
    aws_secret_access_key=settings.R2_SECRET_KEY,
    region_name=          "auto",
)

async def upload_image(image_bytes: bytes, content_type="image/jpeg") -> dict:
    img_hash = hashlib.sha256(image_bytes).hexdigest()
    key      = f"uploads/{img_hash}.jpg"

    try:
        s3.head_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
        # Already exists — skip upload (deduplication)
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            s3.put_object(
                Bucket=     settings.R2_BUCKET_NAME,
                Key=        key,
                Body=       image_bytes,
                ContentType=content_type,
                ACL=        "public-read",
            )

    return {
        "image_url":  f"{settings.CDN_BASE_URL}/{key}",
        "image_hash": img_hash,
    }