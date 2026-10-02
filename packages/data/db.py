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
    from pathlib import Path

    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from packages.data.models import Standard, User

    eng = engine or get_db_engine()
    Base.metadata.create_all(bind=eng)

    with Session(eng) as session:
        user = session.execute(select(User).where(User.username == "officer1")).scalar_one_or_none()
        if not user:
            session.add_all([
                User(
                    username="officer1",
                    hashed_password="hashed_reviewer_password",
                    role="Reviewer",
                    full_name="Procurement Officer",
                ),
                User(
                    username="curator1",
                    hashed_password="hashed_curator_password",
                    role="Curator",
                    full_name="Curator User",
                ),
                User(
                    username="verifier1",
                    hashed_password="hashed_verifier_password",
                    role="Verifier",
                    full_name="Verifier User",
                ),
                User(
                    username="admin1",
                    hashed_password="hashed_admin_password",
                    role="Admin",
                    full_name="Admin User",
                ),
            ])
            session.commit()

        has_std = session.execute(select(Standard)).scalar_one_or_none()
        if not has_std:
            try:
                from packages.data.loader import load_seed_directory

                seed_dir = Path(__file__).resolve().parent / "seed"
                if seed_dir.exists():
                    load_seed_directory(session, seed_dir)
            except Exception:
                pass


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
