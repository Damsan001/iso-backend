import os
from google.cloud import storage
from dotenv import load_dotenv
from fastapi import UploadFile
from datetime import timedelta

load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.path.dirname(__file__), '..', '..', 'cloud-storage.json')
BUCKET_NAME = os.environ['BUCKET_NAME']
storage_client = storage.Client()


def upload_file_to_gcs( file: UploadFile, destination_blob_name: str) -> str:
    """
    Sube un archivo a un bucket de GCS y devuelve la URL pública.
    """
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)

    file_content = file.file.read()

    blob.upload_from_string(file_content, content_type=file.content_type)

    return blob.public_url

def generate_signed_url(blob_name: str) -> str:
    """
    Genera una URL firmada para acceder a un blob en GCS.
    """
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="GET"
    )
    return url