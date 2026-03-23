"""Main orchestration engine for workflow execution."""

import asyncio
import signal
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, TYPE_CHECKING

from croniter import croniter

from .database import Database
from .executor import Executor
from .logger import EngineLogger, WorkflowLogger
from .models import RunStatus, Workflow, RunResult
from .scheduler import Scheduler

if TYPE_CHECKING:
    from .api.websocket import ConnectionManager


class Engine:
    """Main workflow execution engine."""

    def __init__(
        self,
        config_path: str = "config.json",
        db_path: str = "data/workflows.db",
        log_dir: str = "data/logs",
        check_interval: float = 1.0,
        max_concurrent: int = 10
    ):
        """Initialize the workflow engine.

        Args:
            config_path: Path to the JSON configuration file
            db_path: Path to the SQLite database file
            log_dir: Directory for log files
            check_interval: How often to check for due workflows (seconds)
            max_concurrent: Maximum number of concurrent workflow executions
        """
        self.config_path = config_path
        self.check_interval = check_interval
        self.max_concurrent = max_concurrent

        # Initialize components
        self.database = Database(db_path)
        self.workflow_logger = WorkflowLogger(log_dir)
        self.engine_logger = EngineLogger(f"{log_dir}/engine.log")
        self.scheduler = Scheduler()
        self.executor = Executor(self.database, self.workflow_logger)

        # State
        self.workflows: dict[str, Workflow] = {}
        self.running_tasks: set[asyncio.Task] = set()
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._shutdown = False
        self._config_mtime: float = 0

        # Event callbacks for WebSocket broadcasting
        self._event_callbacks: list[Callable[[str, dict], None]] = []

    def add_event_callback(self, callback: Callable[[str, dict], None]) -> None:
        """Add an event callback for WebSocket broadcasting."""
        self._event_callbacks.append(callback)

    def remove_event_callback(self, callback: Callable[[str, dict], None]) -> None:
        """Remove an event callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    async def _emit_event(self, event_type: str, data: dict) -> None:
        """Emit an event to all registered callbacks."""
        # Lazy import to avoid circular dependency
        from .api.websocket import get_manager

        # Also broadcast via WebSocket manager
        try:
            manager = get_manager()
            await manager.broadcast({
                "type": event_type,
                "data": data
            })
        except Exception as e:
            self.engine_logger.error(f"Error broadcasting to WebSocket: {e}")

        # Call registered callbacks
        for callback in self._event_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                self.engine_logger.error(f"Error in event callback: {e}")

    def _validate_workflow(self, data: dict, existing_names: set[str]) -> tuple[bool, str]:
        """Validate a workflow configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if "name" not in data:
            return False, "Missing required field: name"
        if "command" not in data:
            return False, "Missing required field: command"
        if "cron" not in data:
            return False, "Missing required field: cron"

        name = data["name"]

        # Check for duplicate names
        if name in existing_names:
            return False, f"Duplicate workflow name: {name}"

        # Validate cron expression
        try:
            croniter(data["cron"])
        except Exception as e:
            return False, f"Invalid cron expression for '{name}': {e}"

        # Validate optional fields
        if "timeout" in data and data["timeout"] is not None:
            if not isinstance(data["timeout"], int) or data["timeout"] <= 0:
                return False, f"Invalid timeout for '{name}': must be a positive integer"

        if "retry_count" in data:
            if not isinstance(data["retry_count"], int) or data["retry_count"] < 0:
                return False, f"Invalid retry_count for '{name}': must be a non-negative integer"

        if "retry_delay" in data:
            if not isinstance(data["retry_delay"], int) or data["retry_delay"] < 0:
                return False, f"Invalid retry_delay for '{name}': must be a non-negative integer"

        return True, ""

    def load_config(self) -> dict[str, Workflow]:
        """Load workflow configurations from JSON file.

        Returns:
            Dictionary mapping workflow names to Workflow objects
        """
        config_file = Path(self.config_path)

        if not config_file.exists():
            self.engine_logger.error(f"Config file not found: {self.config_path}")
            return {}

        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)

            if not isinstance(config_data, list):
                self.engine_logger.error("Config file must contain a JSON array")
                return {}

            workflows = {}
            seen_names = set()

            for i, item in enumerate(config_data):
                if not isinstance(item, dict):
                    self.engine_logger.warning(f"Config item {i} is not an object, skipping")
                    continue

                # Validate the workflow
                is_valid, error = self._validate_workflow(item, seen_names)
                if not is_valid:
                    self.engine_logger.warning(f"Invalid workflow config: {error}")
                    continue

                try:
                    workflow = Workflow.from_dict(item)
                    workflows[workflow.name] = workflow
                    seen_names.add(workflow.name)
                except (KeyError, ValueError) as e:
                    self.engine_logger.warning(f"Invalid workflow config: {e}")

            self.engine_logger.info(f"Loaded {len(workflows)} workflows from config")

            # Track config modification time for hot-reload
            self._config_mtime = config_file.stat().st_mtime

            return workflows

        except json.JSONDecodeError as e:
            self.engine_logger.error(f"Invalid JSON in config file: {e}")
            return {}

    def initialize_scheduler(self):
        """Initialize the scheduler with all loaded workflows."""
        self.scheduler.reset()
        for workflow in self.workflows.values():
            self.scheduler.initialize_workflow(workflow)

    def check_config_changed(self) -> bool:
        """Check if the config file has been modified since last load."""
        config_file = Path(self.config_path)
        if not config_file.exists():
            return False

        try:
            current_mtime = config_file.stat().st_mtime
            return current_mtime > self._config_mtime
        except OSError:
            return False

    def reload_config(self) -> bool:
        """Reload configuration if it has changed.

        Returns:
            True if config was reloaded, False otherwise
        """
        if not self.check_config_changed():
            return False

        self.engine_logger.info("Detected config file change, reloading...")

        new_workflows = self.load_config()
        if not new_workflows:
            self.engine_logger.warning("Failed to reload config, keeping existing workflows")
            return False

        # Find added, removed, and modified workflows
        old_names = set(self.workflows.keys())
        new_names = set(new_workflows.keys())

        added = new_names - old_names
        removed = old_names - new_names
        # Check for modified workflows (command or cron changed)
        modified = {
            name for name in old_names & new_names
            if (self.workflows[name].command != new_workflows[name].command or
                self.workflows[name].cron != new_workflows[name].cron)
        }

        # Update workflows
        self.workflows = new_workflows

        # Reinitialize scheduler for all workflows
        self.initialize_scheduler()

        # Log changes
        if added:
            self.engine_logger.info(f"Added workflows: {', '.join(added)}")
        if removed:
            self.engine_logger.info(f"Removed workflows: {', '.join(removed)}")
        if modified:
            self.engine_logger.info(f"Modified workflows: {', '.join(modified)}")

        return True

    async def run_workflow_with_retry(self, workflow: Workflow):
        """Run a workflow with retry support."""
        max_attempts = workflow.retry_count + 1
        attempt = 1

        while attempt <= max_attempts:
            # Acquire semaphore to limit concurrency
            async with self._semaphore:
                result = await self.executor.execute(workflow, attempt, max_attempts)

            if result.success:
                self.engine_logger.info(
                    f"Workflow '{workflow.name}' completed successfully "
                    f"(attempt {attempt}/{max_attempts}, duration: {result.duration_seconds:.2f}s)"
                )
                return

            if result.status == RunStatus.TIMEOUT:
                self.engine_logger.error(
                    f"Workflow '{workflow.name}' timed out after {workflow.timeout}s"
                )
            else:
                self.engine_logger.error(
                    f"Workflow '{workflow.name}' failed with exit code {result.exit_code} "
                    f"(attempt {attempt}/{max_attempts})"
                )

            # Check if we should retry
            if attempt < max_attempts:
                self.engine_logger.info(
                    f"Retrying '{workflow.name}' in {workflow.retry_delay}s..."
                )
                await asyncio.sleep(workflow.retry_delay)
                attempt += 1
            else:
                self.engine_logger.error(
                    f"Workflow '{workflow.name}' failed after {max_attempts} attempts"
                )
                return

    async def run_workflow(self, workflow: Workflow):
        """Run a single workflow with semaphore for concurrency control."""
        try:
            await self.run_workflow_with_retry(workflow)
        except Exception as e:
            self.engine_logger.error(f"Error running workflow '{workflow.name}': {e}")

    async def main_loop(self):
        """Main daemon loop."""
        self._semaphore = asyncio.Semaphore(self.max_concurrent)

        self.engine_logger.info("Starting workflow engine")
        self.engine_logger.info(f"Loaded {len(self.workflows)} workflows")
        self.engine_logger.info(f"Max concurrent executions: {self.max_concurrent}")

        # Log next run times
        for workflow in self.workflows.values():
            next_run = self.scheduler.get_next_run_time(workflow)
            if next_run:
                self.engine_logger.info(
                    f"Workflow '{workflow.name}' next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}"
                )

        last_config_check = datetime.now()
        config_check_interval = 5.0  # Check for config changes every 5 seconds

        while not self._shutdown:
            try:
                # Check for config changes periodically
                now = datetime.now()
                if (now - last_config_check).total_seconds() >= config_check_interval:
                    self.reload_config()
                    last_config_check = now

                # Check for due workflows
                due_workflows = self.scheduler.get_due_workflows(list(self.workflows.values()))

                # Spawn tasks for due workflows (with concurrency limit via semaphore)
                for workflow in due_workflows:
                    self.engine_logger.info(f"Workflow '{workflow.name}' is due, starting execution")

                    # Mark as run to update next run time
                    self.scheduler.mark_run(workflow)

                    task = asyncio.create_task(self.run_workflow(workflow))
                    self.running_tasks.add(task)
                    task.add_done_callback(self.running_tasks.discard)

                # Sleep before next check
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                self.engine_logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(self.check_interval)

        # Wait for running tasks to complete on shutdown
        if self.running_tasks:
            self.engine_logger.info(
                f"Waiting for {len(self.running_tasks)} running tasks to complete..."
            )
            await asyncio.gather(*self.running_tasks, return_exceptions=True)

        self.engine_logger.info("Workflow engine stopped")

    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.engine_logger.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # SIGHUP for config reload (Unix only)
        if hasattr(signal, 'SIGHUP'):
            def sighup_handler(signum, frame):
                self.engine_logger.info("Received SIGHUP, reloading config...")
                self.reload_config()
            signal.signal(signal.SIGHUP, sighup_handler)

    def run(self):
        """Run the workflow engine."""
        # Load configuration
        self.workflows = self.load_config()

        if not self.workflows:
            self.engine_logger.warning("No workflows loaded, engine will be idle")

        # Initialize scheduler
        self.initialize_scheduler()

        # Setup signal handlers
        self.setup_signal_handlers()

        # Run the main loop
        try:
            asyncio.run(self.main_loop())
        except KeyboardInterrupt:
            self.engine_logger.info("Keyboard interrupt received")
        finally:
            self.database.close()
            self.engine_logger.info("Engine shutdown complete")

    def get_status(self) -> dict:
        """Get the current status of the engine."""
        return {
            "running": not self._shutdown,
            "workflows_count": len(self.workflows),
            "enabled_workflows": len([w for w in self.workflows.values() if w.enabled]),
            "running_tasks": len(self.running_tasks),
            "max_concurrent": self.max_concurrent,
            "workflows": [
                {
                    "name": w.name,
                    "command": w.command,
                    "cron": w.cron,
                    "enabled": w.enabled,
                    "timeout": w.timeout,
                    "retry_count": w.retry_count,
                    "next_run": self.scheduler.get_next_run_time(w).isoformat()
                        if self.scheduler.get_next_run_time(w) else None
                }
                for w in self.workflows.values()
            ]
        }

    def get_workflow(self, name: str) -> Optional[Workflow]:
        """Get a workflow by name."""
        return self.workflows.get(name)

    def get_recent_runs(
        self,
        workflow_name: Optional[str] = None,
        status: Optional[RunStatus] = None,
        limit: int = 100
    ) -> list:
        """Get recent workflow runs."""
        return self.database.get_recent_runs(workflow_name, status, limit)


    def get_workflow_stats(self, workflow_name: str) -> dict:
        """Get statistics for a workflow."""
        return self.database.get_workflow_stats(workflow_name)
