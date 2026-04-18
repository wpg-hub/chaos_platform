import json
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, execution_id: int):
        await websocket.accept()
        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = set()
        self.active_connections[execution_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, execution_id: int):
        if execution_id in self.active_connections:
            self.active_connections[execution_id].discard(websocket)
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]
    
    async def send_log(self, execution_id: int, level: str, message: str):
        if execution_id in self.active_connections:
            data = json.dumps({
                "level": level,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            for connection in self.active_connections[execution_id]:
                try:
                    await connection.send_text(data)
                except Exception:
                    pass
    
    async def send_status(self, execution_id: int, status: str):
        if execution_id in self.active_connections:
            data = json.dumps({
                "type": "status",
                "status": status,
                "timestamp": datetime.now().isoformat()
            })
            for connection in self.active_connections[execution_id]:
                try:
                    await connection.send_text(data)
                except Exception:
                    pass


manager = ConnectionManager()
