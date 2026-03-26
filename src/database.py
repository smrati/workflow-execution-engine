"""SQLite database operations for workflow execution engine."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from .models import RunStatus, WorkflowRun

if TYPE_CHECKING:
    from .api.auth.models import User


class Database:
    """Handles all SQLite database operations."""

    def __init__(self, db_path: str = "data/workflows.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        """Initialize database tables."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if table exists and needs migration
        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_runs'
        """)
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            # Create new table with all columns
            cursor.execute("""
                CREATE TABLE workflow_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_name TEXT NOT NULL,
                    command TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    exit_code INTEGER,
                    status TEXT NOT NULL DEFAULT 'running',
                    log_file_path TEXT,
                    attempt INTEGER DEFAULT 1
                )
            """)
        else:
            # Check if attempt column exists (migration)
            cursor.execute("PRAGMA table_info(workflow_runs)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'attempt' not in columns:
                cursor.execute("ALTER TABLE workflow_runs ADD COLUMN attempt INTEGER DEFAULT 1")
            
            if 'triggered_by' not in columns:
                cursor.execute("ALTER TABLE workflow_runs ADD COLUMN triggered_by TEXT")

        # Create index for faster queries by workflow name
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_workflow_name 
            ON workflow_runs(workflow_name)
        """)

        # Create index for faster queries by start time
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_start_time 
            ON workflow_runs(start_time)
        """)

        # Create index for status queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status 
            ON workflow_runs(status)
        """)

        conn.commit()

        self._init_users_table(conn)

    def _init_users_table(self, conn):
        """Initialize users table."""
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'normal',
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_username 
            ON users(username)
        """)
        
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'role' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'normal'")
        
        conn.commit()

    def start_run(
        self,
        workflow_name: str,
        command: str,
        log_file_path: str,
        attempt: int = 1,
        triggered_by: Optional[str] = None
    ) -> int:
        """Record the start of a workflow run and return the run ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO workflow_runs 
            (workflow_name, command, start_time, status, log_file_path, attempt, triggered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow_name,
            command,
            datetime.now().isoformat(),
            RunStatus.RUNNING.value,
            log_file_path,
            attempt,
            triggered_by
        ))

        conn.commit()
        return cursor.lastrowid or 0

    def complete_run(
        self,
        run_id: int,
        exit_code: int,
        status: RunStatus
    ):
        """Update a workflow run record with completion details."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE workflow_runs
            SET end_time = ?, exit_code = ?, status = ?
            WHERE id = ?
        """, (
            datetime.now().isoformat(),
            exit_code,
            status.value,
            run_id
        ))

        conn.commit()

    def get_run(self, run_id: int) -> Optional[WorkflowRun]:
        """Get a specific workflow run by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM workflow_runs WHERE id = ?
        """, (run_id,))

        row = cursor.fetchone()
        if row:
            return WorkflowRun.from_dict(dict(row))
        return None

    def get_recent_runs(
        self, 
        workflow_name: Optional[str] = None, 
        status: Optional[RunStatus] = None,
        limit: int = 100
    ) -> list[WorkflowRun]:
        """Get recent workflow runs, optionally filtered by workflow name and/or status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM workflow_runs"
        params = []
        conditions = []

        if workflow_name:
            conditions.append("workflow_name = ?")
            params.append(workflow_name)
        
        if status:
            conditions.append("status = ?")
            params.append(status.value)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [WorkflowRun.from_dict(dict(row)) for row in rows]

    def get_workflow_stats(self, workflow_name: str) -> dict:
        """Get statistics for a specific workflow."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                COUNT(*) as total_runs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_runs,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
                SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeout_runs
            FROM workflow_runs
            WHERE workflow_name = ?
        """, (workflow_name,))

        row = cursor.fetchone()
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
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT workflow_name FROM workflow_runs
            ORDER BY workflow_name
        """)

        return [row["workflow_name"] for row in cursor.fetchall()]

    def cleanup_old_runs(self, days_to_keep: int = 30) -> int:
        """Delete runs older than the specified number of days.
        
        Returns the number of deleted records.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now()
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        cursor.execute("""
            DELETE FROM workflow_runs
            WHERE start_time < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        conn.commit()
        
        return deleted_count

    def create_user(self, username: str, hashed_password: str, role: str = "normal") -> "User":
        """Create a new user and return the User object."""
        from .api.auth.models import User, UserRole
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO users (username, hashed_password, role, created_at)
            VALUES (?, ?, ?, ?)
        """, (username, hashed_password, role, now))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        return User(
            id=user_id,
            username=username,
            hashed_password=hashed_password,
            role=UserRole(role),
            created_at=datetime.fromisoformat(now)
        )

    def get_user_count(self) -> int:
        """Get total number of users."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM users")
        row = cursor.fetchone()
        return row["count"] if row else 0

    def get_all_users(self) -> list["User"]:
        """Get all users (for admin)."""
        from .api.auth.models import User
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [User.from_dict(dict(row)) for row in rows]

    def update_user_role(self, user_id: int, role: str) -> bool:
        """Update a user's role."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET role = ? WHERE id = ?
        """, (role, user_id))
        
        conn.commit()
        return cursor.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0

    def get_user_by_username(self, username: str) -> "User | None":
        """Get a user by username."""
        from .api.auth.models import User
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM users WHERE username = ?
        """, (username,))
        
        row = cursor.fetchone()
        if row:
            return User.from_dict(dict(row))
        return None

    def get_user_by_id(self, user_id: int) -> "User | None":
        """Get a user by ID."""
        from .api.auth.models import User
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM users WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        if row:
            return User.from_dict(dict(row))
        return None

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
