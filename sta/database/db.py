"""SQLAlchemy database setup and session management."""

import os
from .config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager

# Default to SQLite in the project directory

ASYNC_DATABASE_URL = settings.DATABASE_URL
# The sync engine is kept solely for running DDL migrations which might rely on sync execution
# We force the sync engine to use the async dialect path for consistency during migrations
# If this proves problematic, the sync engine setup will need its own path.
# For now, we assume aiosqlite is acceptable for sync PRAGMA commands, otherwise we use sqlite+pysqlite
SYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("aiosqlite", "pysqlite")

engine = create_engine(SYNC_DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)


def run_migrations():
    """Run any pending database migrations."""
    with engine.connect() as conn:
        # Check existing columns in starships table
        result = conn.execute(text("PRAGMA table_info(starships)"))
        columns = [row[1] for row in result.fetchall()]

        # Migration: rename 'registry' to 'ship_registry'
        if "registry" in columns and "ship_registry" not in columns:
            conn.execute(
                text("ALTER TABLE starships RENAME COLUMN registry TO ship_registry")
            )
            conn.commit()
            print(
                "Migration: Renamed 'registry' column to 'ship_registry' in starships table"
            )

        if "shields_raised" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE starships ADD COLUMN shields_raised BOOLEAN DEFAULT 0"
                )
            )
            conn.commit()
            print("Migration: Added shields_raised column to starships table")

        if "weapons_armed" not in columns:
            conn.execute(
                text("ALTER TABLE starships ADD COLUMN weapons_armed BOOLEAN DEFAULT 0")
            )
            conn.commit()
            print("Migration: Added weapons_armed column to starships table")

        # Campaign feature migrations
        # Check existing columns in encounters table
        result = conn.execute(text("PRAGMA table_info(encounters)"))
        encounter_columns = [row[1] for row in result.fetchall()]

        if "campaign_id" not in encounter_columns:
            conn.execute(
                text(
                    "ALTER TABLE encounters ADD COLUMN campaign_id INTEGER REFERENCES campaigns(id)"
                )
            )
            conn.commit()
            print("Migration: Added campaign_id column to encounters table")

        if "status" not in encounter_columns:
            conn.execute(
                text(
                    "ALTER TABLE encounters ADD COLUMN status VARCHAR(20) DEFAULT 'active'"
                )
            )
            conn.commit()
            print("Migration: Added status column to encounters table")

        # Multi-player support migrations
        if "players_turns_used_json" not in encounter_columns:
            conn.execute(
                text(
                    "ALTER TABLE encounters ADD COLUMN players_turns_used_json TEXT DEFAULT '{}'"
                )
            )
            conn.commit()
            print("Migration: Added players_turns_used_json column to encounters table")

        if "current_player_id" not in encounter_columns:
            conn.execute(
                text("ALTER TABLE encounters ADD COLUMN current_player_id INTEGER")
            )
            conn.commit()
            print("Migration: Added current_player_id column to encounters table")

        if "turn_claimed_at" not in encounter_columns:
            conn.execute(
                text("ALTER TABLE encounters ADD COLUMN turn_claimed_at DATETIME")
            )
            conn.commit()
            print("Migration: Added turn_claimed_at column to encounters table")

        if "description" not in encounter_columns:
            conn.execute(text("ALTER TABLE encounters ADD COLUMN description TEXT"))
            conn.commit()
            print("Migration: Added description column to encounters table")

        if "hailing_state_json" not in encounter_columns:
            conn.execute(
                text("ALTER TABLE encounters ADD COLUMN hailing_state_json TEXT")
            )
            conn.commit()
            print("Migration: Added hailing_state_json column to encounters table")

        # GM password migration
        result = conn.execute(text("PRAGMA table_info(campaigns)"))
        campaign_columns = [row[1] for row in result.fetchall()]

        if "gm_password_hash" not in campaign_columns:
            # Default password hash for "ENGAGE1" using werkzeug's pbkdf2:sha256
            # We'll set NULL here and let the app set proper hashes
            conn.execute(
                text("ALTER TABLE campaigns ADD COLUMN gm_password_hash VARCHAR(255)")
            )
            conn.commit()
            print("Migration: Added gm_password_hash column to campaigns table")


def init_db():
    """Initialize the database, creating all tables."""
    from .schema import Base

    Base.metadata.create_all(engine)

    # Run migrations for existing databases
    run_migrations()


def get_session():
    """Get a synchronous database session."""
    return SessionLocal()


async def get_db():
    """Dependency for FastAPI to get an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def async_session_scope():
    """Provide an async transactional scope around a series of operations."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
