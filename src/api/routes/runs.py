"""Run history API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from ..dependencies import get_engine, get_database
from ..schemas import RunResponse, RunListResponse
from ...models import RunStatus
from ...engine import Engine
from ...database import Database

router = APIRouter()


def _run_to_response(run) -> RunResponse:
    """Convert a WorkflowRun to RunResponse."""
    duration = None
    if run.end_time and run.start_time:
        duration = (run.end_time - run.start_time).total_seconds()

    return RunResponse(
        id=run.id,
        workflow_name=run.workflow_name,
        command=run.command,
        start_time=run.start_time,
        end_time=run.end_time,
        exit_code=run.exit_code,
        status=run.status.value if hasattr(run.status, 'value') else run.status,
        log_file_path=run.log_file_path,
        attempt=run.attempt,
        duration_seconds=duration
    )


@router.get("", response_model=RunListResponse)
async def list_runs(
    workflow_name: Optional[str] = Query(None, description="Filter by workflow name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    database: Database = Depends(get_database)
):
    """List workflow runs with optional filtering and pagination."""
    # Parse status filter
    status_filter = None
    if status:
        try:
            status_filter = RunStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be one of: {[s.value for s in RunStatus]}"
            )

    # Get runs (get more than needed to calculate total)
    limit = 1000  # Get a large number to estimate total
    runs = database.get_recent_runs(
        workflow_name=workflow_name,
        status=status_filter,
        limit=limit
    )

    # Calculate pagination
    total = len(runs)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_runs = runs[start_idx:end_idx]

    return RunListResponse(
        runs=[_run_to_response(run) for run in paginated_runs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: int,
    database: Database = Depends(get_database)
):
    """Get details for a specific run."""
    run = database.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return _run_to_response(run)
