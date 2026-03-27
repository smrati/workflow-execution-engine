"""Log access API routes."""

from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends

from ..dependencies import get_database
from ..schemas import LogResponse
from ..auth.dependencies import get_current_user
from ..auth.models import User
from ...db.database import Database

router = APIRouter()


@router.get("/{run_id}", response_model=LogResponse)
async def get_run_log(
    run_id: int,
    database: Database = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get the log content for a specific run."""
    run = database.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    if run.log_file_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"No log file associated with run {run_id}"
        )

    log_path = Path(run.log_file_path)
    content = ""
    exists = log_path.exists()

    if exists:
        try:
            with open(log_path, "r") as f:
                content = f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error reading log file: {str(e)}"
            )

    return LogResponse(
        run_id=run_id,
        workflow_name=run.workflow_name,
        log_file_path=run.log_file_path,
        content=content,
        exists=exists
    )
