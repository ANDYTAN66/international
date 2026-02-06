from __future__ import annotations

import asyncio
from collections.abc import Iterable

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast_json(self, payload: dict) -> None:
        async with self._lock:
            conns: Iterable[WebSocket] = tuple(self._connections)

        stale: list[WebSocket] = []
        for conn in conns:
            try:
                await conn.send_json(payload)
            except Exception:
                stale.append(conn)

        if stale:
            async with self._lock:
                for conn in stale:
                    self._connections.discard(conn)


ws_manager = ConnectionManager()
