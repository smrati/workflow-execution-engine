"""Data models for the workflow execution engine."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class RunStatus(str, Enum):
    """Status of a workflow run."""
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRY = "retry"


@dataclass
class Workflow:
    """Represents a workflow configuration."""
    name: str
    command: str
    cron: str
    enabled: bool = True
    timeout: Optional[int] = None  # Timeout in seconds (None = no timeout)
    retry_count: int = 0  # Number of retries on failure
    retry_delay: int = 60  # Delay between retries in seconds
    working_dir: Optional[str] = None  # Working directory for command execution
    env: Dict[str, str] = field(default_factory=dict)  # Environment variables

    def __post_init__(self):
        """Validate workflow configuration."""
        if not self.name:
            raise ValueError("Workflow name cannot be empty")
        if not self.command:
            raise ValueError("Workflow command cannot be empty")
        if not self.cron:
            raise ValueError("Workflow cron expression cannot be empty")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("Timeout must be a positive integer")
        if self.retry_count < 0:
            raise ValueError("Retry count cannot be negative")
        if self.retry_delay < 0:
            raise ValueError("Retry delay cannot be negative")

    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        """Create a Workflow from a dictionary."""
        return cls(
            name=data["name"],
            command=data["command"],
            cron=data["cron"],
            enabled=data.get("enabled", True),
            timeout=data.get("timeout"),
            retry_count=data.get("retry_count", 0),
            retry_delay=data.get("retry_delay", 60),
            working_dir=data.get("working_dir"),
            env=data.get("env", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Workflow to a dictionary."""
        return {
            "name": self.name,
            "command": self.command,
            "cron": self.cron,
            "enabled": self.enabled,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "working_dir": self.working_dir,
            "env": self.env,
        }


@dataclass
class WorkflowRun:
    """Represents a single execution of a workflow."""
    id: Optional[int]
    workflow_name: str
    command: str
    start_time: datetime
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None
    status: RunStatus = RunStatus.RUNNING
    log_file_path: Optional[str] = None
    attempt: int = 1  # Retry attempt number (1 = first attempt)

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRun":
        """Create a WorkflowRun from a dictionary (e.g., from database row)."""
        return cls(
            id=data.get("id"),
            workflow_name=data["workflow_name"],
            command=data["command"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            exit_code=data.get("exit_code"),
            status=RunStatus(data.get("status", "running")),
            log_file_path=data.get("log_file_path"),
            attempt=data.get("attempt", 1),
        )


@dataclass
class RunResult:
    """Result of a workflow execution."""
    workflow_name: str
    command: str
    start_time: datetime
    end_time: datetime
    exit_code: int
    status: RunStatus
    log_file_path: str
    stdout: str = ""
    stderr: str = ""
    attempt: int = 1
    max_attempts: int = 1

    @property
    def duration_seconds(self) -> float:
        """Calculate the duration of the run in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success(self) -> bool:
        """Check if the run was successful."""
        return self.exit_code == 0

    @property
    def will_retry(self) -> bool:
        """Check if the workflow will be retried."""
        return self.attempt < self.max_attempts and not self.success
