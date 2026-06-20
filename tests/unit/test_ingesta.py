"""Tests unitarios del troceo y utilidades de la ingesta (sin servicios)."""

from scripts.ingest import conninfo_sync, trocear


def test_trocear_pagina_corta_da_un_chunk():
    paginas = [(1, "Una página corta con poco texto.")]
    chunks = trocear(paginas)
    assert len(chunks) == 1
    texto, page = chunks[0]
    assert page == 1
    assert texto.strip() != ""


def test_trocear_preserva_numero_de_pagina():
    paginas = [(3, "Texto de la página tres."), (7, "Texto de la página siete.")]
    chunks = trocear(paginas)
    paginas_resultantes = {page for _, page in chunks}
    assert paginas_resultantes == {3, 7}


def test_trocear_pagina_vacia_no_genera_chunks():
    chunks = trocear([(1, "")])
    assert chunks == []


def test_conninfo_sync_sin_sufijo_de_driver():
    info = conninfo_sync()
    # psycopg.connect no admite el sufijo +driver de SQLAlchemy.
    assert "+psycopg" not in info
    assert "+asyncpg" not in info
    assert info.startswith("postgresql://")
