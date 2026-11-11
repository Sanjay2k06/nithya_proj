"""
Database Session Management and Connection Engine.
"""

from typing import Generator
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.core.config import settings
from backend.core.logging import logger
from backend.db.base import Base

# Ensure directory exists for SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    db_file_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if db_file_path and not db_file_path.startswith(":memory:"):
        Path(db_file_path).resolve().parent.mkdir(parents=True, exist_ok=True)
    Path("./runtime").mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and ensures clean closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Creates database tables if they do not already exist."""
    # Import all models so Base has full metadata
    import backend.models.camera
    import backend.models.detection
    import backend.models.alert
    import backend.models.setting
    import backend.models.notification_log
    import backend.models.environmental_reading
    import backend.models.monitoring_source

    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
