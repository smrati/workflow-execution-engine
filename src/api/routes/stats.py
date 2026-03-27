"""Statistics API routes."""

from fastapi import APIRouter, Depends

from ..dependencies import get_engine, get_database
from ..schemas import (
    EngineStatusResponse,
    WorkflowStatsResponse,
    OverviewStatsResponse,
    RunResponse,
)
from ..auth.dependencies import get_current_user
from ..auth.models import User
from ...engine import Engine
from ...db.database import Database
from ...models import RunStatus

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


@router.get("/engine", response_model=EngineStatusResponse)
async def get_engine_status(
    engine: Engine = Depends(get_engine),
    current_user: User = Depends(get_current_user)
):
    """Get the current status of the engine."""
    uptime = None
    # Try to get uptime from app state if available
    # This would be set in the lifespan handler

    return EngineStatusResponse(
        running=not engine._shutdown,
        workflows_count=len(engine.workflows),
        enabled_workflows=len([w for w in engine.workflows.values() if w.enabled]),
        running_tasks=len(engine.running_tasks),
        max_concurrent=engine.max_concurrent,
        uptime_seconds=uptime
    )


@router.get("/workflows/{name}", response_model=WorkflowStatsResponse)
async def get_workflow_stats(
    name: str,
    engine: Engine = Depends(get_engine),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a specific workflow."""
    workflow = engine.get_workflow(name)
    if workflow is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")

    stats = engine.get_workflow_stats(name)
    total = stats["total_runs"]
    success_rate = (stats["successful_runs"] / total * 100) if total > 0 else 0.0

    return WorkflowStatsResponse(
        workflow_name=name,
        total_runs=stats["total_runs"],
        successful_runs=stats["successful_runs"],
        failed_runs=stats["failed_runs"],
        timeout_runs=stats["timeout_runs"],
        success_rate=round(success_rate, 2)
    )


@router.get("/overview", response_model=OverviewStatsResponse)
async def get_overview_stats(
    engine: Engine = Depends(get_engine),
    database: Database = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard overview statistics."""
    # Get total runs and status breakdown
    all_runs = database.get_recent_runs(limit=10000)
    total_runs = len(all_runs)

    successful = sum(1 for r in all_runs if r.status == RunStatus.SUCCESS)
    failed = sum(
        1 for r in all_runs
        if r.status in [RunStatus.FAILED, RunStatus.TIMEOUT]
    )

    # Get recent runs (last 10)
    recent_runs = all_runs[:10]

    return OverviewStatsResponse(
        total_workflows=len(engine.workflows),
        enabled_workflows=len([w for w in engine.workflows.values() if w.enabled]),
        total_runs=total_runs,
        successful_runs=successful,
        failed_runs=failed,
        recent_runs=[_run_to_response(run) for run in recent_runs],
        running_tasks=len(engine.running_tasks)
    )
