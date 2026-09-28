import os
import uuid

import boto3
from botocore.client import Config


R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")


r2_client = boto3.client(
    "s3",
    endpoint_url=(
        f"https://{R2_ACCOUNT_ID}"
        f".r2.cloudflarestorage.com"
    ),
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto",
    config=Config(
        signature_version="s3v4"
    ),
)


def upload_file(file, folder):

    original_name = file.filename or "image"

    extension = os.path.splitext(
        original_name
    )[1].lower()

    filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    object_key = (
        f"{folder}/{filename}"
    )

    r2_client.upload_fileobj(
        file,
        R2_BUCKET_NAME,
        object_key,
        ExtraArgs={
            "ContentType": (
                file.content_type
                or "application/octet-stream"
            )
        },
    )

    return object_key


def delete_file(object_key):

    if not object_key:
        return

    r2_client.delete_object(
        Bucket=R2_BUCKET_NAME,
        Key=object_key,
    )


def generate_signed_url(
    object_key,
    expires_in=3600
):

    if not object_key:
        return None

    return r2_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": R2_BUCKET_NAME,
            "Key": object_key,
        },
        ExpiresIn=expires_in,
    )