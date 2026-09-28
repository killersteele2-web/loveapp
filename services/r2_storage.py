import os
import uuid

import boto3
from botocore.client import Config


R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")


# ============================================================
# VALIDATE R2 CONFIGURATION
# ============================================================

print("========== R2 CONFIGURATION ==========")
print(
    "R2_ACCOUNT_ID:",
    "SET" if R2_ACCOUNT_ID else "MISSING"
)
print(
    "R2_ACCESS_KEY_ID:",
    "SET" if R2_ACCESS_KEY_ID else "MISSING"
)
print(
    "R2_SECRET_ACCESS_KEY:",
    "SET" if R2_SECRET_ACCESS_KEY else "MISSING"
)
print(
    "R2_BUCKET_NAME:",
    R2_BUCKET_NAME if R2_BUCKET_NAME else "MISSING"
)
print("======================================")


if not R2_ACCOUNT_ID:
    raise RuntimeError(
        "R2_ACCOUNT_ID is missing."
    )

if not R2_ACCESS_KEY_ID:
    raise RuntimeError(
        "R2_ACCESS_KEY_ID is missing."
    )

if not R2_SECRET_ACCESS_KEY:
    raise RuntimeError(
        "R2_SECRET_ACCESS_KEY is missing."
    )

if not R2_BUCKET_NAME:
    raise RuntimeError(
        "R2_BUCKET_NAME is missing."
    )


# ============================================================
# R2 CLIENT
# ============================================================

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


# ============================================================
# UPLOAD
# ============================================================

def upload_file(file, folder):

    if file is None:
        raise ValueError(
            "No file was provided."
        )

    original_name = (
        file.filename or "image"
    )

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

    print(
        f"📤 Uploading to R2: "
        f"{object_key}"
    )

    try:

        # Make sure the stream starts
        # from the beginning.
        file.stream.seek(0)

        r2_client.upload_fileobj(
            file.stream,
            R2_BUCKET_NAME,
            object_key,
            ExtraArgs={
                "ContentType": (
                    file.content_type
                    or "application/octet-stream"
                )
            },
        )

        print(
            f"✅ R2 upload successful: "
            f"{object_key}"
        )

        return object_key

    except Exception as e:

        print(
            f"❌ R2 UPLOAD ERROR: "
            f"{type(e).__name__}: {e}"
        )

        raise


# ============================================================
# DELETE
# ============================================================

def delete_file(object_key):

    if not object_key:
        return

    try:

        r2_client.delete_object(
            Bucket=R2_BUCKET_NAME,
            Key=object_key,
        )

        print(
            f"🗑️ R2 object deleted: "
            f"{object_key}"
        )

    except Exception as e:

        print(
            f"❌ R2 DELETE ERROR: "
            f"{type(e).__name__}: {e}"
        )

        raise


# ============================================================
# SIGNED URL
# ============================================================

def generate_signed_url(
    object_key,
    expires_in=3600
):

    if not object_key:
        return None

    try:

        return r2_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": R2_BUCKET_NAME,
                "Key": object_key,
            },
            ExpiresIn=expires_in,
        )

    except Exception as e:

        print(
            f"❌ R2 SIGNED URL ERROR: "
            f"{type(e).__name__}: {e}"
        )

        return None