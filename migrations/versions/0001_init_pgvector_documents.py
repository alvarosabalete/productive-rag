"""Inicializa pgvector y la tabla de fragmentos del manual.

Revision ID: 0001
Revises:
Create Date: F1 — Datos

Crea:
- la extensión `vector` (pgvector),
- la tabla `documents` (fragmentos del manual + su embedding),
- un índice HNSW con distancia coseno para la búsqueda por similitud.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op
from app.config import get_settings

# Identificadores de la revisión, usados por Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dim = get_settings().embedding_dim

    # Extensión pgvector: aporta el tipo `vector` y los operadores de distancia.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("chunk_text", sa.Text, nullable=False),
        # Vector del fragmento; la dimensión coincide con text-embedding-3-small.
        sa.Column("embedding", Vector(dim), nullable=False),
        # Página de origen (para citar la fuente en las respuestas).
        sa.Column("page", sa.Integer, nullable=True),
        # Orden del fragmento dentro del documento.
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Índice HNSW con operador de distancia coseno (vector_cosine_ops): buena
    # precisión sin paso de entrenamiento, ideal para una sola carga del manual.
    op.execute(
        "CREATE INDEX ix_documents_embedding_hnsw "
        "ON documents USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_index("ix_documents_embedding_hnsw", table_name="documents")
    op.drop_table("documents")
    op.execute("DROP EXTENSION IF EXISTS vector")
