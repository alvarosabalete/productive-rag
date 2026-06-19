"""Punto de entrada de la API (FastAPI app factory)."""

from fastapi import FastAPI

from app.api.routes import health
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="RAG sobre el Manual del Jugador de DnD 5e",
    )

    app.include_router(health.router)

    return app


app = create_app()
