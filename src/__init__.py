"""Workflow Execution Engine - A daemon-based workflow scheduler."""

from .models import Workflow, WorkflowRun, RunResult, RunStatus
from .engine import Engine
from .scheduler import Scheduler
from .executor import Executor
from .db import Database
from .logger import WorkflowLogger, EngineLogger

__version__ = "0.1.0"
__all__ = [
    "Workflow",
    "WorkflowRun",
    "RunResult",
    "RunStatus",
    "Engine",
    "Scheduler",
    "Executor",
    "Database",
    "WorkflowLogger",
    "EngineLogger",
]

# Optional API module
try:
    from .api import create_app
    __all__.append("create_app")
except ImportError:
    pass
