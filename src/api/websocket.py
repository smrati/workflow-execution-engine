"""WebSocket connection manager for real-time updates."""

import asyncio
import json
from datetime import datetime
from typing import Set, Dict, Any, Optional
from fastapi import WebSocket

import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected WebSockets."""
        if not self.active_connections:
            return

        message["timestamp"] = datetime.now().isoformat()

        async with self._lock:
            connections = list(self.active_connections)

        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)

    async def broadcast_run_started(
        self,
        workflow_name: str,
        run_id: int,
        command: str,
        attempt: int = 1
    ):
        """Broadcast a run started event."""
        await self.broadcast({
            "type": "run_started",
            "data": {
                "workflow_name": workflow_name,
                "run_id": run_id,
                "command": command,
                "attempt": attempt
            }
        })

    async def broadcast_run_completed(
        self,
        workflow_name: str,
        run_id: int,
        status: str,
        exit_code: int,
        duration_seconds: float
    ):
        """Broadcast a run completed event."""
        await self.broadcast({
            "type": "run_completed",
            "data": {
                "workflow_name": workflow_name,
                "run_id": run_id,
                "status": status,
                "exit_code": exit_code,
                "duration_seconds": duration_seconds
            }
        })

    async def broadcast_workflow_event(
        self,
        workflow_name: str,
        action: str
    ):
        """Broadcast a workflow change event."""
        await self.broadcast({
            "type": "workflow_event",
            "data": {
                "workflow_name": workflow_name,
                "action": action
            }
        })

    async def broadcast_stats_update(self, stats: Dict[str, Any]):
        """Broadcast a stats update event."""
        await self.broadcast({
            "type": "stats_update",
            "data": stats
        })

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()


def get_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager
