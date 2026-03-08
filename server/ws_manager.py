"""
server/ws_manager.py — WebSocket connection manager.

Quan ly connections theo room (group_id).
Moi group_id = 1 room. Broadcast event cho tat ca members trong room.

Usage:
    from server.ws_manager import ws_manager

    # Trong WebSocket endpoint:
    await ws_manager.connect(websocket, group_id, user_id)
    await ws_manager.disconnect(websocket, group_id)

    # Trong HTTP endpoint (sau khi sync data):
    await ws_manager.broadcast(group_id, {
        "type": "data_updated",
        "data_type": "customers",
        "version": 5,
        "synced_by": "admin",
    })
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass(eq=False)
class ConnectionInfo:
    """Metadata cho moi WebSocket connection."""
    websocket: WebSocket
    user_id: int
    username: str
    group_ids: set[int] = field(default_factory=set)
    connected_at: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)


class WebSocketManager:
    """Quan ly WebSocket connections theo rooms (group_id).

    Thread-safe cho single-worker uvicorn (asyncio).
    Neu scale len multi-worker -> thay bang Redis Pub/Sub.
    """

    def __init__(self) -> None:
        # group_id -> set of ConnectionInfo
        self._rooms: dict[int, set[ConnectionInfo]] = {}
        # websocket -> ConnectionInfo (reverse lookup)
        self._connections: dict[WebSocket, ConnectionInfo] = {}
        # Heartbeat task
        self._heartbeat_task: asyncio.Task | None = None
        # Reference to main event loop (set in start_heartbeat)
        self._loop: asyncio.AbstractEventLoop | None = None

    # -- Connection lifecycle ------------------------------------------------

    async def connect(
        self, ws: WebSocket, user_id: int, username: str, group_ids: list[int],
    ) -> ConnectionInfo:
        """Chap nhan connection va join vao cac rooms."""
        await ws.accept()

        info = ConnectionInfo(
            websocket=ws,
            user_id=user_id,
            username=username,
            group_ids=set(group_ids),
        )
        self._connections[ws] = info

        for gid in group_ids:
            if gid not in self._rooms:
                self._rooms[gid] = set()
            self._rooms[gid].add(info)

        logger.info(
            "WS connected: user=%s groups=%s (total=%d)",
            username, group_ids, len(self._connections),
        )

        # Notify room members
        for gid in group_ids:
            await self._broadcast_presence(gid)

        return info

    async def disconnect(self, ws: WebSocket) -> None:
        """Ngat ket noi va roi tat ca rooms."""
        info = self._connections.pop(ws, None)
        if not info:
            return

        for gid in info.group_ids:
            room = self._rooms.get(gid)
            if room:
                room.discard(info)
                if not room:
                    del self._rooms[gid]
                else:
                    await self._broadcast_presence(gid)

        logger.info(
            "WS disconnected: user=%s (total=%d)",
            info.username, len(self._connections),
        )

    # -- Join/Leave room dynamically ----------------------------------------

    async def join_room(self, ws: WebSocket, group_id: int) -> None:
        """Them connection vao room moi (khi user mo tab nhom khac)."""
        info = self._connections.get(ws)
        if not info:
            return
        info.group_ids.add(group_id)
        if group_id not in self._rooms:
            self._rooms[group_id] = set()
        self._rooms[group_id].add(info)
        await self._broadcast_presence(group_id)

    async def leave_room(self, ws: WebSocket, group_id: int) -> None:
        """Roi room."""
        info = self._connections.get(ws)
        if not info:
            return
        info.group_ids.discard(group_id)
        room = self._rooms.get(group_id)
        if room:
            room.discard(info)
            if not room:
                del self._rooms[group_id]
            else:
                await self._broadcast_presence(group_id)

    # -- Broadcasting -------------------------------------------------------

    async def broadcast(
        self, group_id: int, event: dict[str, Any],
        exclude_ws: WebSocket | None = None,
    ) -> int:
        """Broadcast event cho tat ca connections trong room.

        Returns: so connections da gui thanh cong.
        """
        room = self._rooms.get(group_id)
        if not room:
            return 0

        message = json.dumps(event, default=str)
        sent = 0
        dead: list[ConnectionInfo] = []

        for info in room:
            if info.websocket is exclude_ws:
                continue
            try:
                await info.websocket.send_text(message)
                sent += 1
            except Exception:
                dead.append(info)

        # Cleanup dead connections
        for info in dead:
            room.discard(info)
            self._connections.pop(info.websocket, None)

        return sent

    def broadcast_threadsafe(
        self, group_id: int, event: dict[str, Any],
    ) -> None:
        """Broadcast tu sync context (threadpool). Schedule vao main event loop."""
        if not self._loop:
            return
        asyncio.run_coroutine_threadsafe(
            self.broadcast(group_id, event), self._loop,
        )

    async def send_to_user(self, user_id: int, event: dict[str, Any]) -> int:
        """Gui event cho tat ca connections cua 1 user."""
        message = json.dumps(event, default=str)
        sent = 0
        for info in list(self._connections.values()):
            if info.user_id == user_id:
                try:
                    await info.websocket.send_text(message)
                    sent += 1
                except Exception:
                    pass
        return sent

    # -- Presence -----------------------------------------------------------

    async def _broadcast_presence(self, group_id: int) -> None:
        """Broadcast danh sach members online trong room."""
        room = self._rooms.get(group_id, set())
        # Deduplicate by user_id
        seen: dict[int, dict] = {}
        for info in room:
            seen[info.user_id] = {
                "user_id": info.user_id,
                "username": info.username,
            }

        await self.broadcast(group_id, {
            "type": "presence",
            "group_id": group_id,
            "online": list(seen.values()),
            "count": len(seen),
        })

    def get_online_count(self, group_id: int) -> int:
        """So user online trong room."""
        room = self._rooms.get(group_id, set())
        return len({info.user_id for info in room})

    def get_online_users(self, group_id: int) -> list[dict]:
        """Danh sach user online trong room."""
        room = self._rooms.get(group_id, set())
        seen: dict[int, dict] = {}
        for info in room:
            seen[info.user_id] = {
                "user_id": info.user_id,
                "username": info.username,
            }
        return list(seen.values())

    # -- Heartbeat ----------------------------------------------------------

    async def start_heartbeat(self, interval: int = 30) -> None:
        """Ping tat ca connections moi 30s, cleanup dead ones.
        Also saves reference to main event loop for cross-thread broadcast."""
        self._loop = asyncio.get_running_loop()
        async def _loop() -> None:
            while True:
                await asyncio.sleep(interval)
                dead: list[WebSocket] = []
                for ws, info in list(self._connections.items()):
                    try:
                        await ws.send_json({"type": "ping"})
                        info.last_ping = time.time()
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    await self.disconnect(ws)
                if dead:
                    logger.info("Heartbeat cleaned %d dead connections", len(dead))

        self._heartbeat_task = asyncio.create_task(_loop())

    # -- Stats --------------------------------------------------------------

    @property
    def total_connections(self) -> int:
        return len(self._connections)

    @property
    def total_rooms(self) -> int:
        return len(self._rooms)


# Singleton
ws_manager = WebSocketManager()
