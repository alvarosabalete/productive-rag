# Productive RAG — Manual del Jugador DnD 5e

RAG productivo (autenticación, concurrencia y seguridad) sobre el Manual del
Jugador de DnD 5e. El entorno AWS de producción se simula localmente con
**LocalStack**.

## Arquitectura

```
                    ┌─────────┐
   navegador  ───▶  │  nginx  │  (reverse proxy + frontend estático)
                    └────┬────┘
                         │ /api/*
                    ┌────▼────┐
                    │   api   │  FastAPI (async, JWT, RAG)
                    └──┬───┬──┘
              ┌────────┘   └────────┐──────────────┐
        ┌─────▼─────┐         ┌─────▼─────┐   ┌─────▼─────┐
        │ postgres  │         │   redis   │   │ localstack│
        │ +pgvector │         │  memoria  │   │ S3+Secrets│
        │  (=RDS)   │         │ (=cache)  │   │  (=AWS)   │
        └───────────┘         └───────────┘   └───────────┘

   OpenAI API ── servicio REAL de internet (gpt-5-mini, embeddings)
```

**Decisión clave:** pgvector y Redis corren como contenedores propios (no dentro
de LocalStack), representando RDS/ElastiCache. LocalStack se reserva para los
servicios AWS-nativos: **S3** (almacena el manual) y **Secrets Manager**
(clave OpenAI + credenciales). RDS en LocalStack requeriría la edición Pro y la
extensión pgvector no está garantizada.

## Stack

| Capa            | Tecnología                          |
|-----------------|-------------------------------------|
| API             | FastAPI (async) + Uvicorn           |
| BBDD vectorial  | PostgreSQL + pgvector               |
| Memoria corto   | Redis                               |
| AWS simulado    | LocalStack (S3, Secrets Manager)    |
| LLM/embeddings  | OpenAI `gpt-5-mini` / `text-embedding-3-small` |
| Auth            | JWT propio (OAuth2 password flow)   |
| Frontend        | HTML/CSS/JS                         |
| Reverse proxy   | Nginx                               |
| Entorno Python  | uv                                  |

## Puesta en marcha

```bash
# 1. Configurar entorno
cp .env.example .env      # y rellenar OPENAI_API_KEY

# 2. (Local, sin Docker) instalar dependencias para desarrollo/tests
uv sync

# 3. Levantar todo el stack
docker compose up --build
```

Verificación:

- Frontend: http://localhost:8080
- Health (vía nginx): http://localhost:8080/api/health
- LocalStack health: http://localhost:4566/_localstack/health

## Convención de commits

Este repositorio sigue [Conventional Commits](https://www.conventionalcommits.org):
`<tipo>(<ámbito>): <descripción>` en imperativo y minúscula.

Tipos habituales: `feat` (funcionalidad), `fix` (bug), `chore` (mantenimiento),
`docs` (documentación), `refactor`, `test`, `style`, `ci`, `build`.

```bash
git commit -m "feat(rag): añade endpoint /chat"
git commit -m "chore: configura ruff y .gitattributes"
git commit -m "fix(auth): corrige expiración del token JWT"
```

## Roadmap por fases

- [x] **Fase 0** — Andamiaje: estructura, docker-compose, health.
- [ ] **Fase 1** — Datos: bootstrap S3/Secrets, Alembic, ingesta del manual.
- [ ] **Fase 2** — RAG core: retriever + `/chat`, memoria Redis.
- [ ] **Fase 3** — Auth/Authz: usuarios, JWT, aislamiento de historial.
- [ ] **Fase 4** — Concurrencia y seguridad: workers, rate limiting, pool tuning.
- [ ] **Fase 5** — Carga: Locust + ajustes.
