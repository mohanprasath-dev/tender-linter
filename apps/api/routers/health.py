from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Response, status

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


@router.get("/health/live")
def get_liveness() -> dict[str, str]:
    """Liveness probe: verifies the server process is alive and responsive."""
    return {
        "status": "live",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/ready")
def get_readiness(response: Response) -> dict[str, Any]:
    """Readiness probe: verifies database connectivity and core rule set availability."""
    db_status = check_database_status()
    # Ready if database is connected or configured
    db_ok = "connected" in db_status or "configured" in db_status

    rules_path = settings.BASE_DIR / "packages" / "rules" / "rules.yaml"
    rules_ok = rules_path.exists()

    if not (db_ok and rules_ok):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": db_status,
            "rules_loaded": rules_ok,
            "app_version": settings.APP_VERSION,
        }

    return {
        "status": "ready",
        "database": db_status,
        "rules_loaded": rules_ok,
        "app_version": settings.APP_VERSION,
    }
