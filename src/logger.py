"""Logging system for workflow execution engine."""

import logging
from datetime import datetime
from pathlib import Path


class WorkflowLogger:
    """Handles logging for workflow executions."""

    def __init__(self, base_log_dir: str = "data/logs"):
        """Initialize the logger with a base log directory."""
        self.base_log_dir = Path(base_log_dir)
        self.base_log_dir.mkdir(parents=True, exist_ok=True)

    def get_log_file_path(self, workflow_name: str) -> str:
        """Generate a log file path for a workflow run."""
        # Sanitize workflow name for use in path
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in workflow_name)

        # Create workflow-specific directory
        workflow_log_dir = self.base_log_dir / safe_name
        workflow_log_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{timestamp}.log"

        return str(workflow_log_dir / log_filename)

    def create_run_logger(self, log_file_path: str) -> logging.Logger:
        """Create a logger for a specific workflow run."""
        logger_name = f"workflow_run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        # Remove any existing handlers
        logger.handlers = []

        # File handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        return logger


class EngineLogger:
    """Logger for the workflow engine itself."""

    def __init__(self, log_file: str = "data/logs/engine.log"):
        """Initialize the engine logger."""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("workflow_engine")
        self.logger.setLevel(logging.INFO)

        # Remove any existing handlers
        self.logger.handlers = []

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str):
        """Log an info message."""
        self.logger.info(message)

    def error(self, message: str):
        """Log an error message."""
        self.logger.error(message)

    def warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)

    def debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)
