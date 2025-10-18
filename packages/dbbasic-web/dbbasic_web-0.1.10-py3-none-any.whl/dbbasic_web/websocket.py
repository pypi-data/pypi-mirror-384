"""WebSocket room management"""
import json
from typing import Dict, Set


class WebSocketHub:
    """Manage WebSocket connections and rooms"""

    def __init__(self):
        self.rooms: Dict[str, Set] = {}

    async def join(self, room: str, ws):
        """Add a WebSocket connection to a room"""
        self.rooms.setdefault(room, set()).add(ws)

    async def leave(self, room: str, ws):
        """Remove a WebSocket connection from a room"""
        if room in self.rooms:
            self.rooms[room].discard(ws)
            if not self.rooms[room]:
                del self.rooms[room]

    async def broadcast(self, room: str, event: dict):
        """Broadcast an event to all connections in a room"""
        if room not in self.rooms:
            return

        dead = []
        message = json.dumps(event)

        for ws in self.rooms[room]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            await self.leave(room, ws)

    def get_room_count(self, room: str) -> int:
        """Get the number of connections in a room"""
        return len(self.rooms.get(room, set()))


# Global hub instance
hub = WebSocketHub()
