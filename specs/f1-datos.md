# F1 — Datos: migraciones, clientes cloud e ingesta

## Objetivo

Dejar el manual de D&D 5e troceado, vectorizado y almacenado en Postgres+pgvector,
de forma que F2 (RAG core) solo tenga que buscar por similitud. F1 no responde
preguntas: prepara los datos y las piezas de acceso a la nube que el resto del
proyecto reutilizará.

## Alcance

- **Incluye:**
  - Configuración de Alembic (migraciones versionadas, en español).
  - Migración inicial: `CREATE EXTENSION vector`, tabla `documents` e índice vectorial.
  - Migraciones aplicadas **automáticamente dentro del contenedor `api`** al arrancar
    (imagen autocontenida + entrypoint), no desde el host.
  - Capa de acceso cloud (boto3 → LocalStack): cliente de **Secrets Manager** y de **S3**.
  - Lectura de secretos de negocio (clave OpenAI, credenciales BBDD) desde Secrets Manager.
  - Script de ingesta síncrono (`scripts/ingest.py`): S3 → pypdf → chunking → embeddings → pgvector.
- **No incluye:**
  - Endpoint `/chat` ni retriever (eso es F2).
  - Ingesta event-driven (SQS/Lambda): sigue siendo un script manual.
  - Auth/JWT (F3). Aquí solo se *leen* credenciales, no se gestionan usuarios.
  - Reingesta incremental o detección de cambios en el PDF.

## Enfoque técnico

### 1. Migraciones (Alembic + pgvector)

- `alembic init` adaptado al layout `src/`; carpeta de migraciones en `migrations/`.
- `alembic.ini` + `env.py` leen la URL de BBDD desde `Settings` (`database_url_sync`),
  convertida a driver **síncrono** (`postgresql+psycopg`, psycopg v3) porque Alembic
  corre fuera del event loop. La app sigue usando `asyncpg` en runtime.
- **Ejecución dentro del contenedor**: las migraciones no se lanzan desde el host,
  sino que se aplican solas al arrancar `api` (ver sección "Ejecución de migraciones
  e ingesta" al final).
- Primera migración (`upgrade`):
  - `CREATE EXTENSION IF NOT EXISTS vector;`
  - Tabla `documents`:
    - `id` BIGSERIAL PK
    - `chunk_text` TEXT NOT NULL
    - `embedding` `vector(1536)` NOT NULL (dimensión de `text-embedding-3-small`)
    - `page` INT NULL (página de origen, para citar fuente)
    - `chunk_index` INT NOT NULL (orden del fragmento)
    - `created_at` TIMESTAMPTZ DEFAULT now()
  - Índice vectorial **HNSW** sobre `embedding` con `vector_cosine_ops`
    (distancia coseno; sin paso de entrenamiento, buen recall por defecto).
- `downgrade` revierte tabla, índice y extensión.

### 2. Capa cloud (boto3 → LocalStack)

- Paquete `src/app/cloud/` con tres módulos:
  - `client.py`: `make_client(service)`, factory boto3 compartido contra LocalStack.
  - `secrets.py`: `get_secret`, `get_secret_json`, `get_openai_api_key`,
    `get_db_credentials` (lectura de Secrets Manager).
  - `storage.py`: `download_manual() -> bytes` (`get_object` del PDF en S3).
- Cliente boto3 configurado con `aws_endpoint_url`, `aws_region` y credenciales
  `test/test` desde `Settings`. La config de *infraestructura* (endpoint, región)
  sigue en entorno; lo que se mueve a Secrets Manager son los secretos de *negocio*.
- boto3 es **síncrono**: válido en el script de ingesta (proceso aparte) y en el
  arranque de la app (una vez, fuera del camino de peticiones). No se invoca boto3
  dentro de rutas async.
- Decisión 1A: al recuperar la clave de OpenAI y las credenciales de BBDD, la
  fuente de verdad pasa a ser Secrets Manager. `.env` queda como fallback de
  desarrollo si el secreto no existe.

### 3. Script de ingesta (`scripts/ingest.py`)

Pipeline síncrono, ejecutable **dentro del contenedor**
(`docker compose exec api uv run python scripts/ingest.py`):

```
S3 (get_object) → bytes PDF
  → pypdf: extraer texto por página
  → chunking: ~800 tokens por chunk, ~100 de solape, sin partir a mitad de idea
  → OpenAI embeddings (text-embedding-3-small) en lotes
  → INSERT en documents (texto, vector, page, chunk_index)
```

- Clave de OpenAI recuperada vía Secrets Manager (decisión 1A).
- **Idempotencia (decisión 2A):** borrar y recargar. El script hace `TRUNCATE
  documents` (o `DELETE`) y reinserta desde cero. Para no re-gastar en embeddings
  por accidente, si la tabla ya tiene filas exige el flag `--force`; sin él, avisa
  y aborta.
- Embeddings en lotes para reducir nº de llamadas y coste.
- Conteo de tokens para el tamaño de chunk: vía `tiktoken` (añadir dependencia) o
  aproximación por caracteres si se prefiere no añadir dep. **Decisión abierta.**

## Criterios de aceptación

- [x] Al arrancar el contenedor `api`, el entrypoint aplica `alembic upgrade head`
      y crea la extensión `vector`, la tabla `documents` y el índice HNSW.
      Verificado: con la tabla borrada, al recrear el contenedor la vuelve a crear
      sola (logs `[entrypoint] Aplicando migraciones...` → `Running upgrade -> 0001`).
- [x] La migración es idempotente: reiniciar el contenedor con la migración ya
      aplicada no hace nada (Alembic ve la versión en `alembic_version` y sigue).
- [x] `docker compose exec api uv run alembic downgrade base` revierte limpio
      (roundtrip verificado).
- [x] Existe `get_secret("openai-api-key")` y devuelve el valor guardado en
      LocalStack (test de integración `tests/integration/test_cloud.py`).
- [x] `download_manual()` devuelve los bytes del PDF desde S3 (no del disco local).
- [x] `docker compose exec api uv run python scripts/ingest.py` puebla `documents`
      con N>0 filas; cada fila tiene `embedding` de dimensión 1536.
      Verificado con la clave REAL: 794 filas, todas `vector_dims = 1536`, ninguna
      a cero. La guarda sin `--force` evita re-gastar en embeddings (idempotencia).
- [x] Re-ejecutar la ingesta sin `--force` aborta con aviso; con `--force` borra y
      recarga (TRUNCATE RESTART IDENTITY → sin duplicados).
- [x] `uv run ruff check src scripts tests` y `ruff format --check` pasan.

## Decisiones cerradas durante la implementación

- **Conteo de tokens:** se usa `tiktoken` (`encoding_for_model`) por exactitud.
- **Módulo cloud:** paquete `src/app/cloud/` con `secrets.py`, `storage.py` y un
  `client.py` (factory boto3 compartido, no previsto en el spec inicial).
- **Hosts en `.env`:** `.env` representa el contexto HOST/local y usa `localhost`;
  el contenedor `api` sobrescribe `DATABASE_URL`/`REDIS_URL`/`AWS_ENDPOINT_URL` con
  los hostnames internos de docker-compose. Tras mover migraciones e ingesta al
  contenedor, el único usuario del `.env` desde el host es `uv run pytest` (en
  concreto el test de integración que conecta a LocalStack vía `AWS_ENDPOINT_URL`).
- **Troceo por página:** un chunk no cruza de página, para que la columna `page`
  (atribución de fuente) sea exacta.
- **Nota sobre `db-credentials`:** el secreto guarda `host: postgres` (contexto
  contenedor). El secreto cobra protagonismo cuando la app corra en el contenedor.

## Ejecución de migraciones e ingesta (dentro del contenedor)

Para acercarse a producción, Alembic y la ingesta corren **dentro de la red de
Docker**, no desde el host:

- El `Dockerfile` copia `alembic.ini`, `migrations/` y `scripts/` en la imagen
  (imagen autocontenida).
- `docker-entrypoint.sh` aplica `alembic upgrade head` **al arrancar el contenedor
  `api`** y luego lanza uvicorn. Las migraciones se aplican solas al desplegar.
- La ingesta es una tarea manual:
  `docker compose exec api uv run python scripts/ingest.py`.
- El host (con `.env` → `localhost`) queda solo para tests/utilidades rápidas.
- Límite conocido (a revisar en F4): aplicar migraciones en el arranque de la app
  no escala a varias réplicas de `api` (varias migrarían a la vez). Para un único
  contenedor `api` es correcto; a escala se separaría en un paso/job dedicado.
