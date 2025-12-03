"""SQLAlchemy database setup and session management."""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

# Default to SQLite in the project directory
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "sta_simulator.db"
)

DATABASE_URL = os.environ.get("STA_DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def run_migrations():
    """Run any pending database migrations."""
    with engine.connect() as conn:
        # Check existing columns in starships table
        result = conn.execute(text("PRAGMA table_info(starships)"))
        columns = [row[1] for row in result.fetchall()]

        if 'shields_raised' not in columns:
            conn.execute(text("ALTER TABLE starships ADD COLUMN shields_raised BOOLEAN DEFAULT 0"))
            conn.commit()
            print("Migration: Added shields_raised column to starships table")

        if 'weapons_armed' not in columns:
            conn.execute(text("ALTER TABLE starships ADD COLUMN weapons_armed BOOLEAN DEFAULT 0"))
            conn.commit()
            print("Migration: Added weapons_armed column to starships table")


def init_db():
    """Initialize the database, creating all tables."""
    from .schema import Base
    Base.metadata.create_all(engine)

    # Run migrations for existing databases
    run_migrations()


def get_session() -> Session:
    """Get a new database session."""
    return SessionLocal()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
