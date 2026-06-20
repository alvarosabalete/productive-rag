#!/bin/sh
# Arranque del contenedor api.
# Antes de encender la web, pone la base de datos al día aplicando las
# migraciones de Alembic. Así el esquema siempre está actualizado al desplegar,
# igual que en producción (las migraciones corren DENTRO del sistema, no desde
# el portátil de nadie).
set -e

echo "[entrypoint] Aplicando migraciones (alembic upgrade head)..."
uv run alembic upgrade head

echo "[entrypoint] Base de datos al día. Arrancando la aplicación..."
# exec cede el proceso al CMD (uvicorn), para que reciba bien las señales.
exec "$@"
