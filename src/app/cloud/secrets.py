"""Lectura de secretos de negocio desde AWS Secrets Manager (LocalStack)."""

import json
from typing import Any

from app.cloud.client import make_client
from app.config import get_settings


def get_secret(name: str) -> str:
    """Devuelve el valor (string) de un secreto por su nombre."""
    client = make_client("secretsmanager")
    response = client.get_secret_value(SecretId=name)
    return response["SecretString"]


def get_secret_json(name: str) -> dict[str, Any]:
    """Devuelve un secreto cuyo valor es un JSON, ya parseado."""
    return json.loads(get_secret(name))


def get_openai_api_key() -> str:
    """Recupera la clave de OpenAI.

    Decisión 1A: la fuente de verdad es Secrets Manager. Si no se puede leer
    (p. ej. LocalStack apagado en desarrollo), cae al valor de Settings/.env.
    """
    settings = get_settings()
    try:
        key = get_secret(settings.openai_secret_name)
        if key and key != "sk-placeholder":
            return key
    except Exception:  # noqa: BLE001 — fallback deliberado a .env en local
        pass
    return settings.openai_api_key


def get_db_credentials() -> dict[str, Any]:
    """Recupera las credenciales de la BBDD (JSON en Secrets Manager)."""
    settings = get_settings()
    return get_secret_json(settings.db_secret_name)
