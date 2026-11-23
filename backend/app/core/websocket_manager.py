import json
from datetime import datetime, timezone
from typing import Dict, List, Any
from fastapi import WebSocket


class WebSocketManager:
    """Manages active WebSocket connections for real-time notifications."""

    def __init__(self):
        # user_id -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # websocket -> role
        self.connection_roles: Dict[WebSocket, str] = {}
        # websocket -> user_id
        self.connection_users: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str, role: str) -> None:
        """Register newly accepted WebSocket connection."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.connection_roles[websocket] = role
        self.connection_users[websocket] = user_id

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Unregister closed or disconnected WebSocket connection."""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        self.connection_roles.pop(websocket, None)
        self.connection_users.pop(websocket, None)

    def _format_message(self, event_type: str, data: Any) -> str:
        """Format standardized event payload."""
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return json.dumps(payload, default=str)

    async def broadcast_to_user(self, user_id: str, event_type: str, data: Any) -> None:
        """Send event notification to all active sockets of a specific user."""
        if user_id not in self.active_connections:
            return

        message = self._format_message(event_type, data)
        dead_connections = []
        for socket in self.active_connections[user_id]:
            try:
                await socket.send_text(message)
            except Exception:
                dead_connections.append(socket)

        for socket in dead_connections:
            self.disconnect(socket, user_id)

    async def broadcast_to_role(self, role: str, event_type: str, data: Any) -> None:
        """Send event notification to all users with a specific role."""
        message = self._format_message(event_type, data)
        dead_connections = []
        for socket, socket_role in list(self.connection_roles.items()):
            if socket_role == role:
                try:
                    await socket.send_text(message)
                except Exception:
                    dead_connections.append(socket)

        for socket in dead_connections:
            u_id = self.connection_users.get(socket)
            if u_id:
                self.disconnect(socket, u_id)

    async def broadcast_all(self, event_type: str, data: Any) -> None:
        """Broadcast event to all currently connected clients."""
        message = self._format_message(event_type, data)
        dead_connections = []
        for socket in list(self.connection_roles.keys()):
            try:
                await socket.send_text(message)
            except Exception:
                dead_connections.append(socket)

        for socket in dead_connections:
            u_id = self.connection_users.get(socket)
            if u_id:
                self.disconnect(socket, u_id)


ws_manager = WebSocketManager()
