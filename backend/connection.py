from collections import defaultdict
from fastapi import WebSocket

class ManageConnection:
    def __init__(self):
            self.active_connections: dict[int, set[WebSocket]] = defaultdict(set)

    def connect(self, workspace_id: int, websocket: WebSocket):
        self.active_connections[workspace_id].add(websocket)

    def disconnect(self, workspace_id: int, websocket: WebSocket):
        self.active_connections[workspace_id].discard(websocket)

manager = ManageConnection()