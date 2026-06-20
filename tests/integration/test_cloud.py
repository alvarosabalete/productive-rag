"""Tests de integración de la capa cloud (requieren LocalStack levantado).

Se saltan automáticamente si LocalStack no responde, para no romper la suite en
un entorno sin el stack arrancado.
"""

import socket
from urllib.parse import urlparse

import pytest

from app.cloud.secrets import get_secret
from app.cloud.storage import download_manual
from app.config import get_settings


def _localstack_disponible() -> bool:
    url = urlparse(get_settings().aws_endpoint_url)
    try:
        with socket.create_connection((url.hostname, url.port or 4566), timeout=1):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _localstack_disponible(), reason="LocalStack no está disponible"
)


def test_get_secret_openai_existe():
    valor = get_secret(get_settings().openai_secret_name)
    assert isinstance(valor, str)
    assert valor != ""


def test_download_manual_devuelve_pdf():
    pdf = download_manual()
    assert len(pdf) > 0
    assert pdf[:4] == b"%PDF"
