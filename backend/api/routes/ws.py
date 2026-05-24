import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.fl_bridge import bridge_client

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Push FL status to frontend every 2 seconds
            status = await bridge_client.get_status()
            await websocket.send_json({"type": "status", "data": status})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
