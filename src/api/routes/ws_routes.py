from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from loguru import logger
import json

router = APIRouter(prefix="/ws", tags=["websocket"])

_active_connections: Dict[str, WebSocket] = {}

def get_active_connections() -> Dict[str, WebSocket]:
    return _active_connections

@router.websocket("/{novel_id}")
async def websocket_endpoint(websocket: WebSocket, novel_id: str):
    await websocket.accept()
    _active_connections[novel_id] = websocket
    logger.info(f"WebSocket connected: {novel_id}")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {novel_id}")
    finally:
        _active_connections.pop(novel_id, None)

async def broadcast_to_novel(novel_id: str, message: dict):
    ws = _active_connections.get(novel_id)
    if ws:
        try:
            await ws.send_text(json.dumps(message, ensure_ascii=False, default=str))
        except Exception:
            _active_connections.pop(novel_id, None)
