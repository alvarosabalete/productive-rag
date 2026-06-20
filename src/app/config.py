"""Configuración central de la app.

Lee de variables de entorno (y de .env en local). En despliegue, los secretos
sensibles (clave OpenAI, credenciales BBDD) se recuperarán de AWS Secrets Manager
vía LocalStack; aquí mantenemos los valores por defecto para desarrollo local.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "productive-rag"
    environment: str = "local"

    # OpenAI (servicio real)
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-5-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    # Dimensión del vector que produce text-embedding-3-small (debe coincidir con
    # la columna vector(N) de la tabla documents).
    embedding_dim: int = 1536

    # PostgreSQL + pgvector
    database_url: str = "postgresql+asyncpg://rag:ragpass@postgres:5432/ragdb"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # AWS / LocalStack
    aws_endpoint_url: str = "http://localstack:4566"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    s3_bucket: str = "dnd-manuals"
    s3_manual_key: str = "player-handbook.pdf"
    # Nombres de los secretos en Secrets Manager (secretos de negocio).
    openai_secret_name: str = "openai-api-key"
    db_secret_name: str = "db-credentials"

    # Ingesta / chunking
    chunk_size_tokens: int = 800  # tamaño objetivo de cada fragmento
    chunk_overlap_tokens: int = 100  # solape entre fragmentos contiguos
    embedding_batch_size: int = 64  # nº de chunks por llamada a OpenAI

    # Auth (JWT)
    jwt_secret_key: str = ""
    jwt_algorithm: str = ""
    jwt_access_token_expire_minutes: int = 30

    @property
    def database_url_sync(self) -> str:
        """URL síncrona (psycopg) para Alembic y el script de ingesta.

        El runtime de la app usa asyncpg; Alembic corre fuera del event loop,
        así que necesita un driver síncrono.
        """
        return self.database_url.replace("+asyncpg", "+psycopg")


@lru_cache
def get_settings() -> Settings:
    """Devuelve un único objeto Settings cacheado para toda la app."""
    return Settings()
