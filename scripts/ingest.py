"""Script de ingesta del manual (Fase 1).

Pipeline síncrono y manual (sin SQS/Lambda):

    S3 (get_object) -> bytes PDF
      -> pypdf: extraer texto por página
      -> chunking por tokens (tiktoken), con solape
      -> OpenAI embeddings (text-embedding-3-small) en lotes
      -> INSERT en la tabla documents (pgvector)

Uso (dentro del contenedor, como en producción):
    docker compose exec api uv run python scripts/ingest.py          # carga si vacía
    docker compose exec api uv run python scripts/ingest.py --force  # borra y recarga

Idempotencia (decisión 2A): borrar y recargar. Si la tabla ya tiene filas, el
script aborta salvo que se pase --force, para no re-gastar en embeddings de OpenAI
por accidente.
"""

import argparse
import io
import sys

import psycopg
import tiktoken
from openai import OpenAI
from pgvector.psycopg import register_vector
from pypdf import PdfReader

from app.cloud.secrets import get_openai_api_key
from app.cloud.storage import download_manual
from app.config import get_settings


def conninfo_sync() -> str:
    """URL de conexión para psycopg (sin el sufijo de driver de SQLAlchemy)."""
    return get_settings().database_url_sync.replace("+psycopg", "")


def extraer_paginas(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """Extrae (nº de página, texto) del PDF. Páginas sin texto se descartan."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    paginas: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        texto = (page.extract_text() or "").strip()
        if texto:
            paginas.append((i, texto))
    return paginas


def trocear(paginas: list[tuple[int, str]]) -> list[tuple[str, int]]:
    """Trocea cada página en ventanas de tokens con solape.

    El troceado es por página, así la atribución de fuente (nº de página) es
    exacta y un chunk nunca cruza de una página a otra.

    Devuelve una lista de (texto_del_chunk, nº_de_página).
    """
    settings = get_settings()
    size = settings.chunk_size_tokens
    overlap = settings.chunk_overlap_tokens
    step = size - overlap
    enc = tiktoken.encoding_for_model(settings.openai_embedding_model)

    chunks: list[tuple[str, int]] = []
    for page_num, texto in paginas:
        tokens = enc.encode(texto)
        start = 0
        while start < len(tokens):
            ventana = tokens[start : start + size]
            texto_chunk = enc.decode(ventana).strip()
            if texto_chunk:
                chunks.append((texto_chunk, page_num))
            start += step
    return chunks


def embeddings_en_lotes(textos: list[str], api_key: str) -> list[list[float]]:
    """Calcula embeddings llamando a OpenAI en lotes."""
    settings = get_settings()
    client = OpenAI(api_key=api_key)
    batch = settings.embedding_batch_size
    vectores: list[list[float]] = []
    for i in range(0, len(textos), batch):
        lote = textos[i : i + batch]
        resp = client.embeddings.create(model=settings.openai_embedding_model, input=lote)
        vectores.extend(item.embedding for item in resp.data)
        print(f"  embeddings {min(i + batch, len(textos))}/{len(textos)}")
    return vectores


def contar_filas(conn: psycopg.Connection) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM documents")
        return cur.fetchone()[0]


def insertar(conn: psycopg.Connection, filas: list[tuple[str, list[float], int, int]]) -> None:
    """Vacía la tabla e inserta los chunks (texto, embedding, página, índice)."""
    with conn.cursor() as cur:
        cur.execute("TRUNCATE documents RESTART IDENTITY")
        cur.executemany(
            "INSERT INTO documents (chunk_text, embedding, page, chunk_index) "
            "VALUES (%s, %s, %s, %s)",
            filas,
        )
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingesta del manual de D&D en pgvector.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="borra y recarga aunque la tabla ya tenga datos",
    )
    args = parser.parse_args()

    conn = psycopg.connect(conninfo_sync())
    register_vector(conn)

    existentes = contar_filas(conn)
    if existentes > 0 and not args.force:
        print(
            f"La tabla 'documents' ya tiene {existentes} filas. "
            "Usa --force para borrar y recargar (re-gasta en embeddings de OpenAI)."
        )
        return 1

    api_key = get_openai_api_key()
    if not api_key or api_key in ("", "sk-...", "sk-placeholder"):
        print(
            "No hay una clave de OpenAI válida. Pon la real en .env (OPENAI_API_KEY) "
            "y reinicia LocalStack para que la reescriba en Secrets Manager."
        )
        return 1

    print("1/4 Descargando manual desde S3...")
    pdf_bytes = download_manual()

    print("2/4 Extrayendo texto del PDF...")
    paginas = extraer_paginas(pdf_bytes)
    print(f"     {len(paginas)} páginas con texto")

    print("3/4 Troceando y calculando embeddings...")
    chunks = trocear(paginas)
    print(f"     {len(chunks)} chunks")
    textos = [c[0] for c in chunks]
    vectores = embeddings_en_lotes(textos, api_key)

    print("4/4 Insertando en pgvector (borra y recarga)...")
    filas = [
        (texto, vector, page, idx)
        for idx, ((texto, page), vector) in enumerate(zip(chunks, vectores, strict=True))
    ]
    insertar(conn, filas)

    total = contar_filas(conn)
    conn.close()
    print(f"Listo. La tabla 'documents' tiene {total} filas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
