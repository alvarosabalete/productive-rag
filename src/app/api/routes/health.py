"""Endpoints de salud para verificar que la app y sus dependencias responden."""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Liveness: la app está arriba."""
    settings = get_settings()
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}
