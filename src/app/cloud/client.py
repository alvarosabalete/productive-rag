"""Factory de clientes boto3 apuntando a LocalStack.

La configuración de *infraestructura* (endpoint, región, credenciales de acceso
'test/test') vive en Settings/entorno. Lo que se recupera de Secrets Manager son
los secretos de *negocio* (clave de OpenAI, credenciales de la BBDD).
"""

import boto3

from app.config import get_settings


def make_client(service: str):
    """Crea un cliente boto3 para el servicio dado contra LocalStack."""
    settings = get_settings()
    return boto3.client(
        service,
        endpoint_url=settings.aws_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
