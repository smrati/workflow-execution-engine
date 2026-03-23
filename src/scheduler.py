"""Cron-based scheduler for workflow execution engine."""

from datetime import datetime
from typing import Optional
import logging

from croniter import croniter

from .models import Workflow


class Scheduler:
    """Handles cron-based scheduling for workflows."""

    def __init__(self):
        """Initialize the scheduler."""
        self._cron_iters: dict[str, croniter] = {}
        self._last_run_times: dict[str, datetime] = {}
        self._next_run_times: dict[str, datetime] = {}
        self._logger = logging.getLogger("workflow_engine.scheduler")

    def _get_croniter(self, workflow: Workflow) -> croniter:
        """Get or create a croniter instance for a workflow."""
        if workflow.name not in self._cron_iters:
            try:
                self._cron_iters[workflow.name] = croniter(
                    workflow.cron,
                    start_time=datetime.now()
                )
            except Exception as e:
                self._logger.error(f"Invalid cron expression for '{workflow.name}': {e}")
                raise
        return self._cron_iters[workflow.name]

    def initialize_workflow(self, workflow: Workflow) -> Optional[datetime]:
        """Initialize a workflow and calculate its next run time."""
        if not workflow.enabled:
            return None

        try:
            cron = self._get_croniter(workflow)
            now = datetime.now()
            # Get the next run time from now
            next_run = cron.get_next(datetime)
            self._next_run_times[workflow.name] = next_run
            return next_run
        except Exception:
            return None

    def get_next_run_time(self, workflow: Workflow) -> Optional[datetime]:
        """Get the next scheduled run time for a workflow."""
        if not workflow.enabled:
            return None
        return self._next_run_times.get(workflow.name)

    def is_due(self, workflow: Workflow) -> bool:
        """Check if a workflow is due to run now.
        
        A workflow is due if:
        1. It's enabled
        2. The current time has reached or passed the next scheduled run time
        3. It hasn't already run at this scheduled time
        """
        if not workflow.enabled:
            return False

        next_run = self._next_run_times.get(workflow.name)
        if next_run is None:
            return False

        now = datetime.now()
        # Check if we've reached or passed the next run time
        # Use a 1-second window to account for check intervals
        return now >= next_run

    def mark_run(self, workflow: Workflow) -> datetime:
        """Mark a workflow as run and calculate its next run time.
        
        This should be called AFTER a workflow has been triggered.
        Returns the new next run time.
        """
        try:
            cron = self._get_croniter(workflow)
            now = datetime.now()
            
            # Record the last run time
            self._last_run_times[workflow.name] = now
            
            # Calculate the next run time from now
            next_run = cron.get_next(datetime)
            self._next_run_times[workflow.name] = next_run
            
            return next_run
        except Exception as e:
            self._logger.error(f"Error calculating next run for '{workflow.name}': {e}")
            return None

    def get_due_workflows(self, workflows: list[Workflow]) -> list[Workflow]:
        """Get all workflows that are due to run."""
        due_workflows = []
        for workflow in workflows:
            if self.is_due(workflow):
                due_workflows.append(workflow)
        return due_workflows

    def reset(self):
        """Reset all scheduler state."""
        self._cron_iters.clear()
        self._last_run_times.clear()
        self._next_run_times.clear()

    def remove_workflow(self, workflow_name: str):
        """Remove a workflow from the scheduler."""
        self._cron_iters.pop(workflow_name, None)
        self._last_run_times.pop(workflow_name, None)
        self._next_run_times.pop(workflow_name, None)

    def get_schedule_info(self, workflow: Workflow) -> dict:
        """Get scheduling information for a workflow."""
        return {
            "name": workflow.name,
            "cron": workflow.cron,
            "enabled": workflow.enabled,
            "next_run": self._next_run_times.get(workflow.name).isoformat() 
                if workflow.name in self._next_run_times else None,
            "last_run": self._last_run_times.get(workflow.name).isoformat() 
                if workflow.name in self._last_run_times else None,
        }
