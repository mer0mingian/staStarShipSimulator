"""SQLAlchemy database setup and session management."""

import os
from sqlalchemy import create_engine, text, inspect
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


def validate_schema():
    """
    Validate that the database schema matches the SQLAlchemy models.

    Returns a list of discrepancies (empty list if schema is valid).
    Each discrepancy is a dict with 'type', 'table', and 'message' keys.
    """
    from .schema import Base

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    discrepancies = []

    # Check each table defined in the models
    for table_name, table in Base.metadata.tables.items():
        # Check if table exists
        if table_name not in existing_tables:
            discrepancies.append({
                'type': 'missing_table',
                'table': table_name,
                'message': f"Table '{table_name}' is missing from database"
            })
            continue

        # Table exists, check columns
        actual_columns = {col['name']: col for col in inspector.get_columns(table_name)}
        expected_columns = {col.name: col for col in table.columns}

        for col_name, col in expected_columns.items():
            if col_name not in actual_columns:
                # Determine column type for helpful error message
                col_type = str(col.type)
                nullable = "NULL" if col.nullable else "NOT NULL"

                discrepancies.append({
                    'type': 'missing_column',
                    'table': table_name,
                    'column': col_name,
                    'message': f"Column '{table_name}.{col_name}' ({col_type}, {nullable}) is missing from database"
                })

    return discrepancies


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

        # Campaign feature migrations
        # Check existing columns in encounters table
        result = conn.execute(text("PRAGMA table_info(encounters)"))
        encounter_columns = [row[1] for row in result.fetchall()]

        if 'campaign_id' not in encounter_columns:
            conn.execute(text("ALTER TABLE encounters ADD COLUMN campaign_id INTEGER REFERENCES campaigns(id)"))
            conn.commit()
            print("Migration: Added campaign_id column to encounters table")

        if 'status' not in encounter_columns:
            conn.execute(text("ALTER TABLE encounters ADD COLUMN status VARCHAR(20) DEFAULT 'active'"))
            conn.commit()
            print("Migration: Added status column to encounters table")

        # Multi-player support migrations
        if 'players_turns_used_json' not in encounter_columns:
            conn.execute(text("ALTER TABLE encounters ADD COLUMN players_turns_used_json TEXT DEFAULT '{}'"))
            conn.commit()
            print("Migration: Added players_turns_used_json column to encounters table")

        if 'current_player_id' not in encounter_columns:
            conn.execute(text("ALTER TABLE encounters ADD COLUMN current_player_id INTEGER"))
            conn.commit()
            print("Migration: Added current_player_id column to encounters table")

        if 'turn_claimed_at' not in encounter_columns:
            conn.execute(text("ALTER TABLE encounters ADD COLUMN turn_claimed_at DATETIME"))
            conn.commit()
            print("Migration: Added turn_claimed_at column to encounters table")

        if 'description' not in encounter_columns:
            conn.execute(text("ALTER TABLE encounters ADD COLUMN description TEXT"))
            conn.commit()
            print("Migration: Added description column to encounters table")

        if 'hailing_state_json' not in encounter_columns:
            conn.execute(text("ALTER TABLE encounters ADD COLUMN hailing_state_json TEXT"))
            conn.commit()
            print("Migration: Added hailing_state_json column to encounters table")

        # GM password migration
        result = conn.execute(text("PRAGMA table_info(campaigns)"))
        campaign_columns = [row[1] for row in result.fetchall()]

        if 'gm_password_hash' not in campaign_columns:
            # Default password hash for "ENGAGE1" using werkzeug's pbkdf2:sha256
            # We'll set NULL here and let the app set proper hashes
            conn.execute(text("ALTER TABLE campaigns ADD COLUMN gm_password_hash VARCHAR(255)"))
            conn.commit()
            print("Migration: Added gm_password_hash column to campaigns table")


def init_db():
    """Initialize the database, creating all tables."""
    from .schema import Base
    Base.metadata.create_all(engine)

    # Run migrations for existing databases
    run_migrations()

    # Validate schema after migrations
    discrepancies = validate_schema()

    if discrepancies:
        print("\n" + "="*70)
        print("⚠️  DATABASE SCHEMA MISMATCH DETECTED")
        print("="*70)
        print("\nThe database schema doesn't match your SQLAlchemy models.")
        print("This typically happens when you add new columns to models in")
        print("sta/database/schema.py without updating the database.\n")

        # Group by table for better readability
        tables_affected = {}
        for disc in discrepancies:
            table = disc['table']
            if table not in tables_affected:
                tables_affected[table] = []
            tables_affected[table].append(disc)

        for table, issues in tables_affected.items():
            print(f"\n📋 Table: {table}")
            for issue in issues:
                if issue['type'] == 'missing_table':
                    print(f"   ❌ Table is missing entirely")
                elif issue['type'] == 'missing_column':
                    print(f"   ❌ Missing column: {issue['column']}")

        print("\n" + "-"*70)
        print("💡 HOW TO FIX:")
        print("-"*70)
        print("\n1. Add migrations to run_migrations() in sta/database/db.py")
        print("   For each missing column, add an ALTER TABLE statement like:\n")

        for disc in discrepancies:
            if disc['type'] == 'missing_column':
                table = disc['table']
                column = disc['column']
                print(f"   if '{column}' not in {table}_columns:")
                print(f"       conn.execute(text(\"ALTER TABLE {table} ADD COLUMN {column} ...\"))")
                print(f"       conn.commit()\n")

        print("2. Or delete sta_simulator.db to recreate from scratch:")
        print("   rm sta_simulator.db")
        print("   (WARNING: This deletes all data!)\n")

        print("="*70)
        print("\n⚠️  Continuing startup, but you may encounter SQLAlchemy errors!")
        print("="*70 + "\n")


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
