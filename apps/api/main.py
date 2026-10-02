from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.core.config import settings
from apps.api.routers import health, version

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Evidence-linked auditor for Indian Standards citations in tender specifications",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(version.router, prefix="/api/v1", tags=["version"])

# Mount root aliases for convenience and health probes
app.include_router(health.router, tags=["probes"])
app.include_router(version.router, tags=["probes"])


@app.get("/")
def root() -> dict[str, str]:
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "banner": "This tool flags issues for the officer to review. It does not approve or reject a tender.",
    }
