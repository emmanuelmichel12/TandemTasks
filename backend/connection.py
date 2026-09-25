from collections import defaultdict
from fastapi import WebSocket

class ManageConnection:
    def __init__(self):
        self.active_connections: dict[int, set[WebSocket]] = {}
        self.workspace_users: dict[int, dict[WebSocket, dict]] = {}

    async def connect(self, workspace_id: int, websocket: WebSocket, user: dict):
        await websocket.accept()
        self.active_connections.setdefault(workspace_id, set()).add(websocket)
        self.workspace_users.setdefault(workspace_id, {})[websocket] = user

    def disconnect(self, workspace_id: int, websocket: WebSocket):
        self.active_connections.get(workspace_id, set()).discard(websocket)
        self.workspace_users.get(workspace_id, {}).pop(websocket, None)

    def get_connection_count(self, workspace_id: int) -> int:
        return len(self.active_connections.get(workspace_id, set()))

    def get_workspace_users(self, workspace_id: int) -> list[dict]:
        return list(self.workspace_users.get(workspace_id, {}).values())

    async def broadcast(self, workspace_id: int, message: dict):
        dead_connections = set()
        for connection in self.active_connections.get(workspace_id, set()):
            try:
                await connection.send_text(str(message))
            except Exception:
                dead_connections.add(connection)

            for connection in dead_connections:
                self.disconnect(workspace_id, connection)

manager = ManageConnection()