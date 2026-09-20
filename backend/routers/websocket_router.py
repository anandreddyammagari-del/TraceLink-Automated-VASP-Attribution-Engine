import json
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Set

logger = logging.getLogger("tracelink.websocket")
router = APIRouter(tags=["Live WebSocket Monitoring"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Officer terminal connected to live WebSocket. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"Officer terminal disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        dead_connections = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.active_connections.discard(dead)

ws_manager = ConnectionManager()

@router.websocket("/ws/monitoring")
async def websocket_endpoint(websocket: WebSocket):
    """
    Live real-time monitoring channel for State Cyber Police Command Centers.
    Broadcasts real-time trace completions, sanctions hits, and new transactions.
    """
    await ws_manager.connect(websocket)
    try:
        # Send initial connection acknowledgment
        await websocket.send_text(json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Connected to TraceLink Real-Time Tactical Stream",
            "station": "Special Cyber Operations",
            "channels": ["SANCTIONS_ALERT", "TRACE_UPDATE", "TRANSACTION_INGESTED"]
        }))
        while True:
            # Keep connection open and accept client heartbeats / subscriptions
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                if action == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
