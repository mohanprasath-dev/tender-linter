from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from apps.api.core.config import settings


def get_engine() -> Engine:
    """Create SQLAlchemy engine based on DATABASE_URL setting."""
    connect_args = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(settings.DATABASE_URL, connect_args=connect_args)


def check_database_status() -> str:
    """Check connectivity to configured database (config only for M0)."""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "connected"
    except Exception:
        # For M0, database might not be initialized yet in local environments without Docker
        return f"configured ({settings.DATABASE_URL.split('://')[0]})"
