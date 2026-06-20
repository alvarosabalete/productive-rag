"""Entorno de Alembic.

La URL de la base de datos NO se lee del .ini, sino de la configuración central
de la app (`Settings`), en su variante síncrona (psycopg). Alembic corre fuera
del event loop, por eso no usa asyncpg.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.config import get_settings

# Objeto de configuración de Alembic (acceso a valores del alembic.ini).
config = context.config

# Inyectamos la URL síncrona desde Settings, sobreescribiendo la del .ini.
config.set_main_option("sqlalchemy.url", get_settings().database_url_sync)

# Logging de Python según el .ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No usamos autogenerate: las migraciones (extensión pgvector, tipos vector) se
# escriben a mano con SQL explícito.
target_metadata = None


def run_migrations_offline() -> None:
    """Migraciones en modo 'offline' (genera SQL sin conectar a la BBDD)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Migraciones en modo 'online' (conectando a la BBDD)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
