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

    user = {"id": auth_state.payload["sub"]}

    await manager.connect(workspace_id, websocket, user)

    await websocket.send_json({
        "event": "presence_snapshot",
        "users": manager.get_workspace_users(workspace_id)
    })
    await manager.broadcast(workspace_id, {
        "event": "user_joined",
        "user": user
    })

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(workspace_id, websocket)
        await manager.broadcast(workspace_id, {
            "event": "user_left",
            "user_id": user["id"]
        })