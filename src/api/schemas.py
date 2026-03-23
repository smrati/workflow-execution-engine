"""Pydantic models for API request/response schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ Workflow Schemas ============

class WorkflowBase(BaseModel):
    """Base workflow schema."""
    name: str
    command: str
    cron: str
    enabled: bool = True
    timeout: Optional[int] = None
    retry_count: int = 0
    retry_delay: int = 60
    working_dir: Optional[str] = None
    env: Dict[str, str] = Field(default_factory=dict)


class WorkflowResponse(WorkflowBase):
    """Workflow response with next run time."""
    next_run: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowDetailResponse(WorkflowBase):
    """Detailed workflow response with schedule info."""
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    stats: Optional[Dict[str, int]] = None

    class Config:
        from_attributes = True


class WorkflowTriggerRequest(BaseModel):
    """Request to manually trigger a workflow."""
    pass


class WorkflowEnableRequest(BaseModel):
    """Request to enable/disable a workflow."""
    enabled: bool


# ============ Run Schemas ============

class RunBase(BaseModel):
    """Base run schema."""
    id: Optional[int] = None
    workflow_name: str
    command: str
    start_time: datetime
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None
    status: str
    log_file_path: Optional[str] = None
    attempt: int = 1


class RunResponse(RunBase):
    """Run response schema."""
    duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True


class RunListResponse(BaseModel):
    """Paginated list of runs."""
    runs: List[RunResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RunFilterParams(BaseModel):
    """Filter parameters for run queries."""
    workflow_name: Optional[str] = None
    status: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ============ Stats Schemas ============

class WorkflowStatsResponse(BaseModel):
    """Statistics for a single workflow."""
    workflow_name: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    timeout_runs: int
    success_rate: float


class EngineStatusResponse(BaseModel):
    """Engine status response."""
    running: bool
    workflows_count: int
    enabled_workflows: int
    running_tasks: int
    max_concurrent: int
    uptime_seconds: Optional[float] = None


class OverviewStatsResponse(BaseModel):
    """Dashboard overview statistics."""
    total_workflows: int
    enabled_workflows: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    recent_runs: List[RunResponse]
    running_tasks: int


# ============ Log Schemas ============

class LogResponse(BaseModel):
    """Log file content response."""
    run_id: int
    workflow_name: str
    log_file_path: str
    content: str
    exists: bool


class LogLineResponse(BaseModel):
    """Single log line for streaming."""
    timestamp: str
    level: str
    message: str


# ============ WebSocket Schemas ============

class WSMessage(BaseModel):
    """WebSocket message schema."""
    type: str  # "run_started", "run_completed", "workflow_added", "workflow_removed", "stats_update"
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class RunStartedEvent(BaseModel):
    """Event when a run starts."""
    workflow_name: str
    run_id: int
    command: str
    attempt: int


class RunCompletedEvent(BaseModel):
    """Event when a run completes."""
    workflow_name: str
    run_id: int
    status: str
    exit_code: int
    duration_seconds: float


class WorkflowEvent(BaseModel):
    """Event for workflow changes."""
    workflow_name: str
    action: str  # "added", "removed", "modified", "enabled", "disabled"
