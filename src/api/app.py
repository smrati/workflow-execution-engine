"""FastAPI application factory."""

import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import get_engine
from .websocket import get_manager
from .routes import workflows, runs, stats, logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    startup_time = time.time()
    app.state.startup_time = startup_time
    yield
    # Shutdown
    pass


def create_app(
    title: str = "Workflow Execution Engine API",
    description: str = "REST API for managing and monitoring workflow executions",
    version: str = "0.1.0",
    cors_origins: Optional[list] = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        title: API title
        description: API description
        version: API version
        cors_origins: List of allowed CORS origins

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
    )

    # Configure CORS
    if cors_origins is None:
        cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(
        workflows.router,
        prefix="/api/workflows",
        tags=["workflows"]
    )
    app.include_router(
        runs.router,
        prefix="/api/runs",
        tags=["runs"]
    )
    app.include_router(
        stats.router,
        prefix="/api/stats",
        tags=["stats"]
    )
    app.include_router(
        logs.router,
        prefix="/api/logs",
        tags=["logs"]
    )

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        manager = get_manager()
        await manager.connect(websocket)
        try:
            while True:
                # Keep connection alive and handle any incoming messages
                data = await websocket.receive_text()
                # We can handle client messages here if needed
                # For now, just echo back or ignore
        except WebSocketDisconnect:
            await manager.disconnect(websocket)
        except Exception as e:
            await manager.disconnect(websocket)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Workflow Execution Engine API",
            "version": version,
            "docs": "/docs",
            "openapi": "/openapi.json"
        }

    return app
