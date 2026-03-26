"""Workflow management API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from ..dependencies import get_engine, get_scheduler
from ..schemas import (
    WorkflowResponse,
    WorkflowDetailResponse,
    WorkflowEnableRequest,
)
from ..websocket import get_manager
from ..auth.dependencies import get_current_user, get_current_writable_user
from ..auth.models import User
from ...models import RunStatus
from ...engine import Engine
from ...scheduler import Scheduler

router = APIRouter()


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    enabled_only: bool = False,
    engine: Engine = Depends(get_engine),
    current_user: User = Depends(get_current_user)
):
    """List all workflows."""
    workflows = []
    for workflow in engine.workflows.values():
        if enabled_only and not workflow.enabled:
            continue

        next_run = engine.scheduler.get_next_run_time(workflow)
        workflows.append(WorkflowResponse(
            name=workflow.name,
            command=workflow.command,
            cron=workflow.cron,
            enabled=workflow.enabled,
            timeout=workflow.timeout,
            retry_count=workflow.retry_count,
            retry_delay=workflow.retry_delay,
            working_dir=workflow.working_dir,
            env=workflow.env,
            next_run=next_run
        ))

    return workflows


@router.get("/{name}", response_model=WorkflowDetailResponse)
async def get_workflow(
    name: str,
    engine: Engine = Depends(get_engine),
    current_user: User = Depends(get_current_user)
):
    """Get details for a specific workflow."""
    workflow = engine.get_workflow(name)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")

    schedule_info = engine.scheduler.get_schedule_info(workflow)
    stats = engine.get_workflow_stats(name)

    return WorkflowDetailResponse(
        name=workflow.name,
        command=workflow.command,
        cron=workflow.cron,
        enabled=workflow.enabled,
        timeout=workflow.timeout,
        retry_count=workflow.retry_count,
        retry_delay=workflow.retry_delay,
        working_dir=workflow.working_dir,
        env=workflow.env,
        next_run=schedule_info.get("next_run"),
        last_run=schedule_info.get("last_run"),
        stats=stats
    )


@router.get("/{name}/schedule")
async def get_workflow_schedule(
    name: str,
    engine: Engine = Depends(get_engine),
    current_user: User = Depends(get_current_user)
):
    """Get schedule information for a workflow."""
    workflow = engine.get_workflow(name)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")

    return engine.scheduler.get_schedule_info(workflow)


@router.post("/{name}/run")
async def trigger_workflow_run(
    name: str,
    engine: Engine = Depends(get_engine),
    current_user: User = Depends(get_current_writable_user)
):
    """Manually trigger a workflow run."""
    workflow = engine.get_workflow(name)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")

    if not workflow.enabled:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow '{name}' is disabled. Enable it first."
        )

    # Create a task to run the workflow
    import asyncio
    task = asyncio.create_task(engine.run_workflow(workflow, triggered_by=current_user.username))

    return {
        "message": f"Workflow '{name}' triggered",
        "workflow_name": name
    }


@router.put("/{name}/enable")
async def enable_workflow(
    name: str,
    engine: Engine = Depends(get_engine),
    current_user: User = Depends(get_current_writable_user)
):
    """Enable a workflow."""
    workflow = engine.get_workflow(name)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")

    workflow.enabled = True
    engine.scheduler.initialize_workflow(workflow)

    # Broadcast event
    manager = get_manager()
    await manager.broadcast_workflow_event(name, "enabled")

    return {
        "message": f"Workflow '{name}' enabled",
        "workflow_name": name,
        "enabled": True
    }


@router.put("/{name}/disable")
async def disable_workflow(
    name: str,
    engine: Engine = Depends(get_engine),
    current_user: User = Depends(get_current_writable_user)
):
    """Disable a workflow."""
    workflow = engine.get_workflow(name)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")

    workflow.enabled = False

    # Broadcast event
    manager = get_manager()
    await manager.broadcast_workflow_event(name, "disabled")

    return {
        "message": f"Workflow '{name}' disabled",
        "workflow_name": name,
        "enabled": False
    }
