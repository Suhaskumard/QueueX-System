"""
QueueMind — WebSocket Connection Manager
-----------------------------------------
Manages active WebSocket connections and broadcasts
real-time events to connected dashboard clients.
"""

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("queuemind.websocket")


class ConnectionManager:
    """
    WebSocket connection manager for real-time dashboard updates.
    Handles connect/disconnect and broadcasts events to all clients.
    """

    def __init__(self):
        self._active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active_connections.append(websocket)
        logger.info(f"[WS] Client connected. Total: {len(self._active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
        logger.info(f"[WS] Client disconnected. Total: {len(self._active_connections)}")

    @property
    def connection_count(self) -> int:
        return len(self._active_connections)

    async def broadcast(self, event_type: str, data: Any) -> None:
        """Broadcast an event to all connected clients."""
        message = json.dumps({
            "type": event_type,
            "data": data if isinstance(data, dict) else data.model_dump() if hasattr(data, 'model_dump') else str(data),
            "timestamp": datetime.utcnow().isoformat(),
        })

        disconnected = []
        for connection in self._active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        # Clean up dead connections
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, event_type: str, data: Any) -> None:
        """Send a message to a specific client."""
        message = json.dumps({
            "type": event_type,
            "data": data if isinstance(data, dict) else data.model_dump() if hasattr(data, 'model_dump') else str(data),
            "timestamp": datetime.utcnow().isoformat(),
        })
        try:
            await websocket.send_text(message)
        except Exception:
            self.disconnect(websocket)
