"""Health check endpoint."""

from fastapi import APIRouter
from backend.app.config import settings
from backend.app.schemas.simulation import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Check backend operational health status."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
    )
