"""Async command executor for workflow execution engine."""

import asyncio
import os
from datetime import datetime
from typing import Optional

from .database import Database
from .logger import WorkflowLogger
from .models import RunResult, RunStatus, Workflow


class Executor:
    """Handles async execution of workflow commands."""

    def __init__(self, database: Database, workflow_logger: WorkflowLogger):
        """Initialize the executor."""
        self.database = database
        self.workflow_logger = workflow_logger

    async def execute(
        self, 
        workflow: Workflow, 
        attempt: int = 1,
        max_attempts: int = 1
    ) -> RunResult:
        """Execute a workflow command asynchronously.
        
        Args:
            workflow: The workflow to execute
            attempt: Current attempt number (1-indexed)
            max_attempts: Maximum number of attempts (including retries)
        
        Returns:
            RunResult with execution details
        """
        start_time = datetime.now()
        
        # Generate log file path
        log_file_path = self.workflow_logger.get_log_file_path(workflow.name)
        
        # Create run logger
        run_logger = self.workflow_logger.create_run_logger(log_file_path)
        
        # Log start
        run_logger.info(f"Starting workflow: {workflow.name}")
        run_logger.info(f"Command: {workflow.command}")
        run_logger.info(f"Attempt: {attempt}/{max_attempts}")
        if workflow.timeout:
            run_logger.info(f"Timeout: {workflow.timeout}s")
        if workflow.working_dir:
            run_logger.info(f"Working directory: {workflow.working_dir}")
        if workflow.env:
            run_logger.info(f"Environment variables: {list(workflow.env.keys())}")
        
        # Record run start in database
        run_id = self.database.start_run(
            workflow_name=workflow.name,
            command=workflow.command,
            log_file_path=log_file_path,
            attempt=attempt
        )
        
        stdout_text = ""
        stderr_text = ""
        exit_code = 0
        status = RunStatus.SUCCESS
        
        try:
            # Prepare environment
            env = os.environ.copy()
            if workflow.env:
                env.update(workflow.env)
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                workflow.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True,
                cwd=workflow.working_dir,
                env=env
            )
            
            # Capture output with timeout
            try:
                if workflow.timeout:
                    stdout_text, stderr_text = await asyncio.wait_for(
                        self._read_streams(process, run_logger),
                        timeout=workflow.timeout
                    )
                else:
                    stdout_text, stderr_text = await self._read_streams(process, run_logger)
                
                exit_code = process.returncode
                
            except asyncio.TimeoutError:
                # Kill the process on timeout
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass
                
                run_logger.error(f"Command timed out after {workflow.timeout}s")
                status = RunStatus.TIMEOUT
                exit_code = -1
                stderr_text = f"Command timed out after {workflow.timeout} seconds"
                
        except Exception as e:
            run_logger.error(f"Error executing command: {e}")
            stderr_text = str(e)
            exit_code = 1
            status = RunStatus.FAILED
        
        end_time = datetime.now()
        
        # Determine final status
        if status != RunStatus.TIMEOUT:
            status = RunStatus.SUCCESS if exit_code == 0 else RunStatus.FAILED
        
        # Check if we should retry
        if status == RunStatus.FAILED and attempt < max_attempts:
            status = RunStatus.RETRY
            run_logger.warning(f"Will retry (attempt {attempt + 1}/{max_attempts})")
        
        # Log completion
        run_logger.info(f"Workflow completed with exit code: {exit_code}")
        run_logger.info(f"Status: {status.value}")
        run_logger.info(f"Duration: {(end_time - start_time).total_seconds():.2f} seconds")
        
        # Update database
        self.database.complete_run(
            run_id=run_id,
            exit_code=exit_code,
            status=status
        )
        
        return RunResult(
            workflow_name=workflow.name,
            command=workflow.command,
            start_time=start_time,
            end_time=end_time,
            exit_code=exit_code,
            status=status,
            log_file_path=log_file_path,
            stdout=stdout_text,
            stderr=stderr_text,
            attempt=attempt,
            max_attempts=max_attempts
        )

    async def _read_streams(self, process, logger) -> tuple[str, str]:
        """Read from both stdout and stderr streams."""
        async def read_stream(stream, prefix: str) -> str:
            lines = []
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded_line = line.decode("utf-8", errors="replace").rstrip()
                lines.append(decoded_line)
                logger.info(f"[{prefix}] {decoded_line}")
            return "\n".join(lines)
        
        stdout_task = asyncio.create_task(read_stream(process.stdout, "STDOUT"))
        stderr_task = asyncio.create_task(read_stream(process.stderr, "STDERR"))
        
        stdout_text, stderr_text = await asyncio.gather(stdout_task, stderr_task)
        exit_code = await process.wait()
        
        return stdout_text, stderr_text
