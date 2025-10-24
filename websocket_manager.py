# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。

"""
WebSocket 连接管理器
"""

from typing import Dict, Set
import asyncio
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if job_id not in self._connections:
                self._connections[job_id] = set()
            self._connections[job_id].add(websocket)
    
    async def disconnect(self, job_id: str, websocket: WebSocket):
        async with self._lock:
            if job_id in self._connections and websocket in self._connections[job_id]:
                self._connections[job_id].remove(websocket)
            if job_id in self._connections and not self._connections[job_id]:
                del self._connections[job_id]
    
    async def broadcast(self, job_id: str, message: str):
        async with self._lock:
            connections = list(self._connections.get(job_id, set()))
        
        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception:
                await self.disconnect(job_id, websocket)
    
    async def broadcast_system(self, message: str):
        async with self._lock:
            all_connections = [ws for conns in self._connections.values() for ws in conns]
        
        for websocket in all_connections:
            try:
                await websocket.send_text(message)
            except Exception:
                # 无法确定 job_id，只能关闭连接
                await websocket.close()


websocket_manager = WebSocketManager()
