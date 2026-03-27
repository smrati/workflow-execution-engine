"""Database operations using SQLAlchemy Core with async support."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    create_engine,
    text,
    Table,
    Column,
    Integer,
    String,
    MetaData,
    Index,
    select,
    insert,
    update,
    delete,
    func,
    case,
)
from sqlalchemy.engine import Engine

from ..models import RunStatus, WorkflowRun

if TYPE_CHECKING:
    from ..api.auth.models import User

metadata = MetaData()

workflow_runs = Table(
    "workflow_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("workflow_name", String, nullable=False),
    Column("command", String, nullable=False),
    Column("start_time", String, nullable=False),
    Column("end_time", String, nullable=True),
    Column("exit_code", Integer, nullable=True),
    Column("status", String, nullable=False, default="running"),
    Column("log_file_path", String, nullable=True),
    Column("attempt", Integer, default=1),
    Column("triggered_by", String, nullable=True),
)

Index("idx_workflow_name", workflow_runs.c.workflow_name)
Index("idx_start_time", workflow_runs.c.start_time)
Index("idx_status", workflow_runs.c.status)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String, nullable=False, unique=True),
    Column("hashed_password", String, nullable=False),
    Column("role", String, nullable=False, default="normal"),
    Column("created_at", String, nullable=False),
)

Index("idx_users_username", users.c.username)


class Database:
    """Handles all database operations via SQLAlchemy Core.

    Supports SQLite (default) and PostgreSQL via the DATABASE_URL
    environment variable or constructor parameter.

    Examples:
        sqlite:  sqlite+aiosqlite:///data/workflows.db
        postgres: postgresql+asyncpg://user:pass@localhost:5432/dbname
    """

    def __init__(self, database_url: str = "sqlite+aiosqlite:///data/workflows.db"):
        self.database_url = database_url
        self._sync_url = self._make_sync_url(database_url)
        self._ensure_db_directory()
        self._engine: Engine = create_engine(self._sync_url)
        self._init_db()

    def _ensure_db_directory(self):
        """Ensure the database directory exists (SQLite only)."""
        if self._sync_url.startswith("sqlite"):
            db_path = self._sync_url.split(":///")[-1]
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _make_sync_url(url: str) -> str:
        """Convert an async database URL to a sync one for SQLAlchemy Core."""
        if url.startswith("sqlite+aiosqlite:///"):
            return "sqlite:///" + url.split(":///")[-1]
        if url.startswith("postgresql+asyncpg://"):
            return "postgresql://" + url.split("://")[-1]
        return url

    def _is_sqlite(self) -> bool:
        return self._sync_url.startswith("sqlite")

    def _init_db(self):
        """Create tables if they don't exist and run migrations."""
        metadata.create_all(self._engine)

        if self._is_sqlite():
            self._migrate_sqlite()

    def _migrate_sqlite(self):
        """Run SQLite-specific migrations for columns added after initial schema."""
        import sqlite3

        db_path = self._sync_url.split(":///")[-1]
        if not os.path.exists(db_path):
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA table_info(workflow_runs)")
            existing_cols = [col[1] for col in cursor.fetchall()]
            if "triggered_by" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE workflow_runs ADD COLUMN triggered_by TEXT"
                )
        finally:
            conn.commit()
            conn.close()

    def _execute(self, query, params=None):
        """Execute a statement and return the result proxy."""
        with self._engine.connect() as conn:
            result = conn.execute(query, params or {})
            conn.commit()
            return result

    def _fetchone(self, query, params=None):
        """Execute and return a single row as dict."""
        with self._engine.connect() as conn:
            result = conn.execute(query, params or {})
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None

    def _fetchall(self, query, params=None):
        """Execute and return all rows as list of dicts."""
        with self._engine.connect() as conn:
            result = conn.execute(query, params or {})
            return [dict(row._mapping) for row in result.fetchall()]

    def start_run(
        self,
        workflow_name: str,
        command: str,
        log_file_path: str,
        attempt: int = 1,
        triggered_by: Optional[str] = None,
    ) -> int:
        """Record the start of a workflow run and return the run ID."""
        stmt = insert(workflow_runs).values(
            workflow_name=workflow_name,
            command=command,
            start_time=datetime.now().isoformat(),
            status=RunStatus.RUNNING.value,
            log_file_path=log_file_path,
            attempt=attempt,
            triggered_by=triggered_by,
        )
        result = self._execute(stmt)
        return result.lastrowid or 0

    def complete_run(self, run_id: int, exit_code: int, status: RunStatus):
        """Update a workflow run record with completion details."""
        stmt = (
            update(workflow_runs)
            .where(workflow_runs.c.id == run_id)
            .values(
                end_time=datetime.now().isoformat(),
                exit_code=exit_code,
                status=status.value,
            )
        )
        self._execute(stmt)

    def get_run(self, run_id: int) -> Optional[WorkflowRun]:
        """Get a specific workflow run by ID."""
        stmt = select(workflow_runs).where(workflow_runs.c.id == run_id)
        row = self._fetchone(stmt)
        if row:
            return WorkflowRun.from_dict(row)
        return None

    def get_recent_runs(
        self,
        workflow_name: Optional[str] = None,
        status: Optional[RunStatus] = None,
        limit: int = 100,
    ) -> list[WorkflowRun]:
        """Get recent workflow runs, optionally filtered."""
        stmt = select(workflow_runs)
        conditions = []

        if workflow_name:
            conditions.append(workflow_runs.c.workflow_name == workflow_name)
        if status:
            conditions.append(workflow_runs.c.status == status.value)

        if conditions:
            from sqlalchemy import and_
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(workflow_runs.c.start_time.desc()).limit(limit)
        rows = self._fetchall(stmt)
        return [WorkflowRun.from_dict(row) for row in rows]

    def get_workflow_stats(self, workflow_name: str) -> dict:
        """Get statistics for a specific workflow."""
        stmt = (
            select(
                func.count(workflow_runs.c.id).label("total_runs"),
                func.sum(
                    case((workflow_runs.c.status == "success", 1), else_=0)
                ).label("successful_runs"),
                func.sum(
                    case((workflow_runs.c.status == "failed", 1), else_=0)
                ).label("failed_runs"),
                func.sum(
                    case((workflow_runs.c.status == "timeout", 1), else_=0)
                ).label("timeout_runs"),
            )
            .where(workflow_runs.c.workflow_name == workflow_name)
        )
        row = self._fetchone(stmt)
        if row:
            return {
                "total_runs": row["total_runs"] or 0,
                "successful_runs": row["successful_runs"] or 0,
                "failed_runs": row["failed_runs"] or 0,
                "timeout_runs": row["timeout_runs"] or 0,
            }
        return {"total_runs": 0, "successful_runs": 0, "failed_runs": 0, "timeout_runs": 0}

    def get_all_workflow_names(self) -> list[str]:
        """Get a list of all unique workflow names that have been run."""
        stmt = (
            select(workflow_runs.c.workflow_name)
            .distinct()
            .order_by(workflow_runs.c.workflow_name)
        )
        rows = self._fetchall(stmt)
        return [row["workflow_name"] for row in rows]

    def delete_runs_by_date_range(
        self,
        before: Optional[str] = None,
        after: Optional[str] = None,
        workflow_name: Optional[str] = None,
    ) -> dict:
        """Delete workflow runs by date range and optionally by workflow name.

        Also deletes associated log files from disk.
        """
        from sqlalchemy import and_

        conditions = []
        if before:
            conditions.append(workflow_runs.c.start_time < before)
        if after:
            conditions.append(workflow_runs.c.start_time > after)
        if workflow_name:
            conditions.append(workflow_runs.c.workflow_name == workflow_name)

        if not conditions:
            return {"deleted_count": 0, "deleted_log_files": 0, "errors": []}

        where = and_(*conditions)

        select_stmt = select(
            workflow_runs.c.id, workflow_runs.c.log_file_path
        ).where(where)
        rows = self._fetchall(select_stmt)

        deleted_log_files = 0
        errors = []

        for row in rows:
            log_path = row.get("log_file_path")
            if log_path:
                try:
                    if os.path.exists(log_path):
                        os.remove(log_path)
                        deleted_log_files += 1
                except Exception as e:
                    errors.append(f"Failed to delete log file {log_path}: {e}")

        delete_stmt = delete(workflow_runs).where(where)
        result = self._execute(delete_stmt)

        return {
            "deleted_count": result.rowcount,
            "deleted_log_files": deleted_log_files,
            "errors": errors,
        }

    def cleanup_old_runs(self, days_to_keep: int = 30) -> int:
        """Delete runs older than the specified number of days."""
        cutoff = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        stmt = delete(workflow_runs).where(workflow_runs.c.start_time < cutoff)
        result = self._execute(stmt)
        return result.rowcount

    def create_user(
        self, username: str, hashed_password: str, role: str = "normal"
    ) -> "User":
        """Create a new user and return the User object."""
        from ..api.auth.models import User, UserRole

        now = datetime.now().isoformat()
        stmt = insert(users).values(
            username=username,
            hashed_password=hashed_password,
            role=role,
            created_at=now,
        )
        result = self._execute(stmt)

        return User(
            id=result.lastrowid,
            username=username,
            hashed_password=hashed_password,
            role=UserRole(role),
            created_at=datetime.fromisoformat(now),
        )

    def get_user_count(self) -> int:
        """Get total number of users."""
        stmt = select(func.count(users.c.id))
        row = self._fetchone(stmt)
        return row["count_1"] if row else 0

    def get_all_users(self) -> list["User"]:
        """Get all users (for admin)."""
        from ..api.auth.models import User

        stmt = select(users).order_by(users.c.created_at.desc())
        rows = self._fetchall(stmt)
        return [User.from_dict(row) for row in rows]

    def update_user_role(self, user_id: int, role: str) -> bool:
        """Update a user's role."""
        stmt = update(users).where(users.c.id == user_id).values(role=role)
        result = self._execute(stmt)
        return result.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        stmt = delete(users).where(users.c.id == user_id)
        result = self._execute(stmt)
        return result.rowcount > 0

    def get_user_by_username(self, username: str) -> "User | None":
        """Get a user by username."""
        from ..api.auth.models import User

        stmt = select(users).where(users.c.username == username)
        row = self._fetchone(stmt)
        if row:
            return User.from_dict(row)
        return None

    def get_user_by_id(self, user_id: int) -> "User | None":
        """Get a user by ID."""
        from ..api.auth.models import User

        stmt = select(users).where(users.c.id == user_id)
        row = self._fetchone(stmt)
        if row:
            return User.from_dict(row)
        return None

    def close(self):
        """Dispose the database engine."""
        self._engine.dispose()
