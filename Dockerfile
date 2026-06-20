# Imagen de la API (FastAPI) construida con uv.
FROM python:3.11-slim

# uv: gestor de entorno y dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# curl para healthchecks; build-essential no hace falta (ruedas binarias)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# 1) Instalar dependencias (capa cacheable)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2) Copiar el código e instalar el proyecto (README.md lo necesita hatchling)
COPY README.md ./README.md
COPY src ./src
RUN uv sync --frozen --no-dev

# 3) Migraciones, scripts e ingesta: la imagen es autocontenida (todo lo que el
#    contenedor necesita para migrar/ingestar va dentro de ella).
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
COPY scripts ./scripts
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh

EXPOSE 8000

# El entrypoint aplica las migraciones y luego lanza el CMD (uvicorn).
ENTRYPOINT ["./docker-entrypoint.sh"]

# Varios workers para concurrencia; FastAPI es async dentro de cada worker.
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
