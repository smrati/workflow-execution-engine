"""Database package with SQLAlchemy Core backend."""

import os
from .database import Database

_db_instance: Database | None = None


def init_database(database_url: str | None = None) -> Database:
    """Initialize and return the global database instance.

    Args:
        database_url: SQLAlchemy database URL. Defaults to DATABASE_URL
                      env var, then sqlite+aiosqlite:///data/workflows.db
    """
    global _db_instance

    if database_url is None:
        database_url = os.environ.get(
            "DATABASE_URL",
            "sqlite+aiosqlite:///data/workflows.db"
        )

    _db_instance = Database(database_url)
    return _db_instance


def get_database() -> Database:
    """Return the initialized database instance."""
    if _db_instance is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_instance
