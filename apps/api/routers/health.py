from fastapi import APIRouter

from apps.api.core.config import settings
from apps.api.core.database import check_database_status
from apps.api.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return application health status and database connectivity info."""
    return HealthResponse(
        status="ok",
        app=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database=check_database_status(),
    )
