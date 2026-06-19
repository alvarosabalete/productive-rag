# CLAUDE.md

Guía para trabajar en este repositorio. Léela antes de proponer cambios.

## Qué es

RAG productivo sobre el **Manual del Jugador de DnD 5e**. Es un proyecto de
aprendizaje: el objetivo no es solo el RAG, sino practicar un despliegue
"productivo" — conexión entre servicios cloud, autenticación/autorización,
concurrencia multiusuario sin degradar, y seguridad. El entorno AWS se simula
localmente con **LocalStack**.

Responde siempre en **español**.

## Arquitectura (decisiones cerradas — no reabrir sin avisar)

- **pgvector y Redis son contenedores propios** en `docker-compose`, **NO dentro
  de LocalStack**. Representan RDS y ElastiCache. Motivo: RDS en LocalStack exige
  edición Pro y la extensión `pgvector` no está garantizada.
- **LocalStack solo simula** S3 (almacena el manual) y Secrets Manager (clave de
  OpenAI + credenciales de BBDD).
- **OpenAI es un servicio real de internet** (no se simula): chat `gpt-5-mini`,
  embeddings `text-embedding-3-small`.
- **Auth: JWT propio** en FastAPI (OAuth2 password flow), no Cognito.
- **RAG: custom/minimal** con SQL directo sobre pgvector. Sin LangChain/LlamaIndex.
- **Multiusuario:** manual compartido + historial privado por usuario (Redis).
- **Ingesta:** básica/síncrona vía script (S3 → trocea → embeddings → pgvector).
  Sin event-driven (SQS/Lambda) por ahora.

```
navegador → nginx (proxy + frontend) → api (FastAPI async)
                                         ├─ postgres+pgvector  (=RDS)
                                         ├─ redis              (=cache)
                                         └─ localstack         (S3 + Secrets)
api → OpenAI API (real, internet)
```

## Stack

FastAPI async + Uvicorn (workers) tras Nginx · SQLAlchemy async + asyncpg +
Alembic · pgvector · Redis · boto3 · OpenAI SDK · frontend HTML/CSS/JS ·
**uv** para el entorno · Locust para carga.

## Estructura

```
src/app/              # paquete de la app (layout src, instalado editable por hatchling)
  config.py           # Settings (pydantic-settings); lee de .env / entorno
  main.py             # app factory FastAPI
  api/routes/         # endpoints (health.py; pendientes: auth, chat)
infra/localstack/init # scripts de bootstrap AWS (se ejecutan al arrancar LocalStack)
infra/nginx           # nginx.conf
frontend/             # index.html, styles.css, app.js
data/                 # player-handbook.pdf (gitignored: copyright + binario)
migrations/           # Alembic (pendiente, Fase 1)
tests/                # pytest (unit, integration, load)
```

## Comandos

```bash
# Entorno local (desarrollo y tests)
uv sync                      # instala deps + crea .venv y uv.lock
uv run pytest                # tests
uv run ruff check src        # lint
uv run ruff format src       # formato

# Stack completo
docker compose up --build -d # levanta todo
docker compose ps            # estado
docker compose logs -f api   # logs de la API
docker compose down          # parar (conserva datos)
docker compose down -v       # parar y BORRAR volúmenes (resetea BBDD/S3)

# Inspeccionar LocalStack
docker compose exec localstack awslocal s3 ls s3://dnd-manuals
docker compose exec localstack awslocal secretsmanager list-secrets
```

Verificación rápida: http://localhost:8080/api/health · docs: `/api/docs`

## Convenciones

- **uv para todo**; nunca `pip install` suelto. Dependencias en `pyproject.toml`,
  `uv.lock` se versiona.
- Python **async** de punta a punta (FastAPI, asyncpg, redis async). No metas
  llamadas bloqueantes en rutas async.
- **Secretos fuera del código**: vía Secrets Manager (LocalStack) o `.env`. `.env`
  NO se versiona; mantén `.env.example` al día al añadir variables.
- Config nueva → añádela a `src/app/config.py` (`Settings`) y a `.env.example`.
- En `docker-compose`, los hosts internos son los nombres de servicio
  (`postgres`, `redis`, `localstack`), no `localhost`.
- Comentarios y mensajes de cara al usuario en español.

## Commits

Usar **Conventional Commits**: `<tipo>(<ámbito opcional>): <descripción>`. La
descripción en minúscula, en imperativo y concisa.

Tipos:

| Tipo | Cuándo |
|---|---|
| `feat` | nueva funcionalidad |
| `fix` | corrección de un bug |
| `chore` | mantenimiento (deps, config, tareas que no tocan código de negocio) |
| `docs` | solo documentación |
| `refactor` | reestructurar código sin cambiar comportamiento |
| `test` | añadir o corregir tests |
| `style` | formato (espacios, comas…), sin cambio de lógica |
| `ci` | configuración de CI/CD |
| `build` | sistema de build, Docker, dependencias del empaquetado |

Ejemplos: `feat(rag): añade endpoint /chat`, `chore: configura ruff`,
`fix(auth): corrige expiración del token JWT`.

**IMPORTANTE — autoría:** el repositorio es exclusivamente del usuario. Cuando
Claude genere un commit, **NO** debe añadir el trailer `Co-Authored-By` ni
ninguna referencia que lo haga figurar como autor, contribuidor o colaborador.

## Roadmap

- [x] **F0** Andamiaje: estructura, docker-compose, /health.
- [ ] **F1** Datos: Alembic + extensión pgvector, cliente S3/Secrets, script de ingesta.
- [ ] **F2** RAG core: retriever + `/chat`, memoria Redis.
- [ ] **F3** Auth/Authz: usuarios, JWT, aislamiento de historial.
- [ ] **F4** Concurrencia y seguridad: workers, rate limiting, pool tuning, CORS/headers.
- [ ] **F5** Carga: Locust + ajustes.

## Notas

- Entorno: Windows 11, Docker Desktop, uv 0.11, Python 3.11.9. La shell por
  defecto es PowerShell (sintaxis distinta de bash).
- La key de OpenAI en `.env` es un placeholder hasta F1/F2; entonces hará falta
  la real y reiniciar LocalStack para que la reescriba en Secrets Manager.
