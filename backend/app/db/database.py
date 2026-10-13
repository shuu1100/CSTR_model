"""SQLAlchemy 2.x SQLite engine and session configuration.

Adheres strictly to GLOBAL-INSTRUCTIONS.md and phase-12:
- Fully offline SQLite engine.
- Thread-safe session generator for FastAPI dependency injection.
- Automatic table initialization.
"""

from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.config import settings

# Ensure parent directory for database exists
db_url = settings.database_url
if db_url.startswith("sqlite:///"):
    db_path_str = db_url.replace("sqlite:///", "")
    db_path = Path(db_path_str)
    db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 ORM models."""
    pass


def init_db() -> None:
    """Initialize all database tables defined on Base and apply lightweight migrations."""
    Base.metadata.create_all(bind=engine)
    if "sqlite" in settings.database_url:
        with engine.connect() as conn:
            try:
                from sqlalchemy import text
                result = conn.execute(text("PRAGMA table_info(simulation_runs)"))
                cols = {row[1] for row in result.fetchall()}
                if cols:
                    if "schema_version" not in cols:
                        conn.execute(text("ALTER TABLE simulation_runs ADD COLUMN schema_version VARCHAR(16) DEFAULT '1.0'"))
                    if "artifact_ref" not in cols:
                        conn.execute(text("ALTER TABLE simulation_runs ADD COLUMN artifact_ref VARCHAR(256)"))
                    if "seed" not in cols:
                        conn.execute(text("ALTER TABLE simulation_runs ADD COLUMN seed INTEGER"))
                    if "split_id" not in cols:
                        conn.execute(text("ALTER TABLE simulation_runs ADD COLUMN split_id VARCHAR(64)"))
                    conn.commit()
            except Exception:
                pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
