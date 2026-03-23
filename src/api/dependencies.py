"""FastAPI dependencies for accessing the workflow engine."""

from typing import Optional
from functools import lru_cache

from ..engine import Engine


# Global engine instance (set by the application)
_engine_instance: Optional[Engine] = None


def set_engine(engine: Engine):
    """Set the global engine instance."""
    global _engine_instance
    _engine_instance = engine


def get_engine() -> Engine:
    """Get the engine instance.

    Raises:
        RuntimeError: If engine has not been set
    """
    if _engine_instance is None:
        raise RuntimeError("Engine not initialized. Call set_engine() first.")
    return _engine_instance


def get_database():
    """Get the database from the engine."""
    return get_engine().database


def get_scheduler():
    """Get the scheduler from the engine."""
    return get_engine().scheduler
