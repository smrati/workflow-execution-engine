"""Combined engine and API server entry point.

This runs both the workflow engine and the API server in the same process.
"""

import argparse
import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional

import uvicorn
from uvicorn import Config, Server

from src.api.app import create_app
from src.api.dependencies import set_engine
from src.api.websocket import get_manager
from src.engine import Engine


class CombinedRunner:
    """Runs both the workflow engine and API server together."""

    def __init__(
        self,
        config_path: str = "config.json",
        db_path: str = "data/workflows.db",
        log_dir: str = "data/logs",
        api_host: str = "0.0.0.0",
        api_port: int = 8000,
        check_interval: float = 1.0,
        max_concurrent: int = 10
    ):
        """Initialize the combined runner."""
        self.config_path = config_path
        self.db_path = db_path
        self.log_dir = log_dir
        self.api_host = api_host
        self.api_port = api_port
        self.check_interval = check_interval
        self.max_concurrent = max_concurrent

        self.engine: Optional[Engine] = None
        self.server: Optional[Server] = None
        self._shutdown = False
        self.startup_time: Optional[datetime] = None

    async def broadcast_event(self, event_type: str, data: dict):
        """Broadcast an event via WebSocket."""
        manager = get_manager()
        await manager.broadcast({
            "type": event_type,
            "data": data
        })

    async def run_engine(self):
        """Run the workflow engine main loop."""
        self.engine._semaphore = asyncio.Semaphore(self.engine.max_concurrent)

        self.engine.engine_logger.info("Starting workflow engine")
        self.engine.engine_logger.info(f"Loaded {len(self.engine.workflows)} workflows")
        self.engine.engine_logger.info(f"Max concurrent executions: {self.engine.max_concurrent}")

        # Log next run times
        for workflow in self.engine.workflows.values():
            next_run = self.engine.scheduler.get_next_run_time(workflow)
            if next_run:
                self.engine.engine_logger.info(
                    f"Workflow '{workflow.name}' next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}"
                )

        last_config_check = datetime.now()
        config_check_interval = 5.0

        while not self._shutdown:
            try:
                # Check for config changes
                now = datetime.now()
                if (now - last_config_check).total_seconds() >= config_check_interval:
                    if self.engine.reload_config():
                        # Broadcast workflow changes
                        await self.broadcast_event("workflows_reloaded", {
                            "count": len(self.engine.workflows)
                        })
                    last_config_check = now

                # Check for due workflows
                due_workflows = self.engine.scheduler.get_due_workflows(
                    list(self.engine.workflows.values())
                )

                for workflow in due_workflows:
                    self.engine.engine_logger.info(
                        f"Workflow '{workflow.name}' is due, starting execution"
                    )

                    self.engine.scheduler.mark_run(workflow)

                    # Start the workflow task
                    task = asyncio.create_task(
                        self.run_workflow_with_broadcast(workflow)
                    )
                    self.engine.running_tasks.add(task)
                    task.add_done_callback(self.engine.running_tasks.discard)

                await asyncio.sleep(self.engine.check_interval)

            except Exception as e:
                self.engine.engine_logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(self.engine.check_interval)

        # Wait for running tasks
        if self.engine.running_tasks:
            self.engine.engine_logger.info(
                f"Waiting for {len(self.engine.running_tasks)} running tasks..."
            )
            await asyncio.gather(*self.engine.running_tasks, return_exceptions=True)

        self.engine.engine_logger.info("Workflow engine stopped")

    async def run_workflow_with_broadcast(self, workflow):
        """Run a workflow and broadcast events."""
        from src.models import RunStatus

        max_attempts = workflow.retry_count + 1
        attempt = 1

        while attempt <= max_attempts:
            async with self.engine._semaphore:
                result = await self.engine.executor.execute(
                    workflow, attempt, max_attempts
                )

                # Broadcast run completed event
                await self.broadcast_event("run_completed", {
                    "workflow_name": workflow.name,
                    "run_id": self.engine.database.get_run(
                        self.engine.database._get_connection()
                        .execute(
                            "SELECT id FROM workflow_runs WHERE log_file_path = ?",
                            (result.log_file_path,)
                        ).fetchone()[0]
                    ).id if result.log_file_path else None,
                    "status": result.status.value,
                    "exit_code": result.exit_code,
                    "duration_seconds": result.duration_seconds
                })

            if result.success:
                self.engine.engine_logger.info(
                    f"Workflow '{workflow.name}' completed successfully "
                    f"(attempt {attempt}/{max_attempts}, duration: {result.duration_seconds:.2f}s)"
                )
                return

            if result.status == RunStatus.TIMEOUT:
                self.engine.engine_logger.error(
                    f"Workflow '{workflow.name}' timed out after {workflow.timeout}s"
                )
            else:
                self.engine.engine_logger.error(
                    f"Workflow '{workflow.name}' failed with exit code {result.exit_code} "
                    f"(attempt {attempt}/{max_attempts})"
                )

            if attempt < max_attempts:
                self.engine.engine_logger.info(
                    f"Retrying '{workflow.name}' in {workflow.retry_delay}s..."
                )
                await asyncio.sleep(workflow.retry_delay)
                attempt += 1
            else:
                self.engine.engine_logger.error(
                    f"Workflow '{workflow.name}' failed after {max_attempts} attempts"
                )
                return

    async def run(self):
        """Run both the engine and API server."""
        self.startup_time = datetime.now()

        # Initialize engine
        self.engine = Engine(
            config_path=self.config_path,
            db_path=self.db_path,
            log_dir=self.log_dir,
            check_interval=self.check_interval,
            max_concurrent=self.max_concurrent
        )
        self.engine.workflows = self.engine.load_config()
        self.engine.initialize_scheduler()

        # Set engine for API
        set_engine(self.engine)

        # Create FastAPI app
        app = create_app()

        # Store startup time in app state
        @app.middleware("http")
        async def add_uptime(request, call_next):
            return await call_next(request)

        app.state.startup_time = self.startup_time

        # Configure uvicorn
        config = Config(
            app=app,
            host=self.api_host,
            port=self.api_port,
            loop="asyncio"
        )
        self.server = Server(config)

        # Setup signal handlers
        def signal_handler(signum, frame):
            self._shutdown = True
            self.engine._shutdown = True
            self.engine.engine_logger.info(f"Received signal {signum}, shutting down...")

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run both tasks
        engine_task = asyncio.create_task(self.run_engine())

        self.engine.engine_logger.info(
            f"Starting API server on {self.api_host}:{self.api_port}"
        )

        try:
            # Run the server (this will block until shutdown)
            await self.server.serve()
        except Exception as e:
            self.engine.engine_logger.error(f"API server error: {e}")
        finally:
            self._shutdown = True
            self.engine._shutdown = True
            await engine_task
            self.engine.database.close()
            self.engine.engine_logger.info("Combined runner shutdown complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Workflow Engine with API Server")
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to workflow configuration file"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="data/workflows.db",
        help="Path to SQLite database"
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="data/logs",
        help="Directory for log files"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="API server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port (default: 8000)"
    )
    parser.add_argument(
        "--check-interval",
        type=float,
        default=1.0,
        help="Workflow check interval in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=10,
        help="Maximum concurrent workflow executions (default: 10)"
    )

    args = parser.parse_args()

    runner = CombinedRunner(
        config_path=args.config,
        db_path=args.db_path,
        log_dir=args.log_dir,
        api_host=args.host,
        api_port=args.port,
        check_interval=args.check_interval,
        max_concurrent=args.max_concurrent
    )

    asyncio.run(runner.run())


if __name__ == "__main__":
    main()
