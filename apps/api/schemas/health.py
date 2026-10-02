from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    app: str
    environment: str
    database: str
