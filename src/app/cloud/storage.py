"""Acceso a S3 (LocalStack) para el manual de D&D."""

from app.cloud.client import make_client
from app.config import get_settings


def download_manual() -> bytes:
    """Descarga el PDF del manual desde S3 y devuelve sus bytes.

    En producción el manual vive en S3, no en el disco local; la ingesta debe
    leerlo de ahí para ser fiel al despliegue.
    """
    settings = get_settings()
    client = make_client("s3")
    response = client.get_object(Bucket=settings.s3_bucket, Key=settings.s3_manual_key)
    return response["Body"].read()
