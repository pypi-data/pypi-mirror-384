import os
from hestia_earth.utils.storage._s3_client import _get_s3_client


def _get_bucket() -> str: return os.getenv('AWS_BUCKET_DISTRIBUTION')


def _write_to_bucket(bucket: str, key: str, body, content_type: str):
    _get_s3_client().put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        # ContentType=content_type
    )
