from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.core.config import settings
from apps.api.routers import admin, audits, auth, health, products, standards, version
from packages.data.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown events."""
    try:
        init_db()
    except Exception:
        # Allow running in testing or environments where DB might connect later
        pass
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Evidence-linked auditor for Indian Standards citations in tender specifications",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(version.router, prefix="/api/v1", tags=["version"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(standards.router, prefix="/api/v1", tags=["standards"])
app.include_router(products.router, prefix="/api/v1", tags=["products"])
app.include_router(audits.router, prefix="/api/v1", tags=["audits"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])

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
