from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from apps.api.core.config import settings
from packages.data.models import Base


def get_db_engine(database_url: str | None = None) -> Engine:
    """Create database engine supporting SQLite and PostgreSQL."""
    url = database_url or settings.DATABASE_URL
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args)


def init_db(engine: Engine | None = None) -> None:
    """Create all tables in the database if they do not exist."""
    eng = engine or get_db_engine()
    Base.metadata.create_all(bind=eng)


def get_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    eng = engine or get_db_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=eng)


def get_db() -> Generator[Session, None, None]:
    """Dependency for yielding database sessions."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
