from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from auth import require_auth_ws
from connection import manager

router = APIRouter()

@router.websocket("/ws/{workspace_id}")
async def workspace_socket(websocket: WebSocket, workspace_id: int):
    token = websocket.query_params.get("token")
    auth_state = require_auth_ws(token)

    if auth_state is None:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    manager.connect(workspace_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(workspace_id, websocket)