import os
from hestia_earth.utils.storage._azure_client import _get_blob_service_client


def _get_container() -> str: return os.getenv('AZURE_STORAGE_CONTAINER_DISTRIBUTION')


def _write_to_container(container: str, key: str, body):
    from azure.core.exceptions import ResourceNotFoundError
    try:
        blob_client = _get_blob_service_client().get_blob_client(container=container, blob=key)
        return blob_client.upload_blob(body)
    except ResourceNotFoundError:
        return None
