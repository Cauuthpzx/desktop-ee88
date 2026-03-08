# KIẾN TRÚC WEBSOCKET — REALTIME DATA SYNC

---

## VẤN ĐỀ CẦN GIẢI QUYẾT TRƯỚC

### workers=4 không tương thích WebSocket

```python
# Hiện tại:
uvicorn.run("server.main:app", host="0.0.0.0", port=8000, workers=4)
```

**Vấn đề:** 4 workers = 4 process riêng biệt. Client A kết nối worker 1, 
Client B kết nối worker 3 → chúng **không thấy nhau**.

**Giải pháp:** 2 cách:

```
Cách 1 (ĐƠN GIẢN - Recommended cho VPS nhỏ):
  workers=1 + asyncio event loop
  → Tất cả WebSocket connections trong cùng 1 process
  → Đủ cho ~200 concurrent connections
  → VPS 1 CPU vẫn OK vì WebSocket hầu như idle

Cách 2 (SCALE LỚN - Khi cần):
  workers=4 + Redis Pub/Sub làm message broker
  → Worker 1 publish → Redis → Worker 3 nhận → broadcast
  → Cần cài Redis trên VPS
```

**Recommendation:** Bắt đầu với Cách 1. Khi nào >200 users mới cần Redis.

```python
# server/main.py — SỬA:
if __name__ == "__main__":
    from server.database import init_schema
    init_schema()
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, workers=1)
    #                                                          ^^^^^^^^
    # workers=1 cho WebSocket. Dùng --workers 1 trong systemd service.
```

---

## TỔNG QUAN KIẾN TRÚC

```
                    ┌──────────────────────────────────────────┐
                    │            FastAPI Server                 │
                    │                                          │
 ┌─────────┐  WS   │  ┌──────────────────────────────────┐   │
 │Client A ├───────>│  │  WebSocketManager                │   │
 │(Admin)  │<───────│  │                                  │   │
 └─────────┘       │  │  rooms:                          │   │
                    │  │    group_5: [ws_A, ws_B, ws_C]  │   │
 ┌─────────┐  WS   │  │    group_8: [ws_D, ws_E]        │   │
 │Client B ├───────>│  │                                  │   │
 │(Member) │<───────│  │  broadcast(group_id, event)     │   │
 └─────────┘       │  │    → send to all in room         │   │
                    │  └──────────────────────────────────┘   │
 ┌─────────┐  WS   │                                          │
 │Client C ├───────>│  HTTP endpoints (giữ nguyên)            │
 │(Member) │<───────│  + POST /api/groups/{id}/sync           │
 └─────────┘       │    → lưu cache → ws_manager.broadcast() │
                    └──────────────────────────────────────────┘
```

---

## SERVER-SIDE: WEBSOCKET MANAGER

### File mới: `server/ws_manager.py`

```python
"""
server/ws_manager.py — WebSocket connection manager.

Quản lý connections theo room (group_id).
Mỗi group_id = 1 room. Broadcast event cho tất cả members trong room.

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


@dataclass
class ConnectionInfo:
    """Metadata cho mỗi WebSocket connection."""
    websocket: WebSocket
    user_id: int
    username: str
    group_ids: set[int] = field(default_factory=set)
    connected_at: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)


class WebSocketManager:
    """Quản lý WebSocket connections theo rooms (group_id).
    
    Thread-safe cho single-worker uvicorn (asyncio).
    Nếu scale lên multi-worker → thay bằng Redis Pub/Sub.
    """

    def __init__(self) -> None:
        # group_id → set of ConnectionInfo
        self._rooms: dict[int, set[ConnectionInfo]] = {}
        # websocket → ConnectionInfo (reverse lookup)
        self._connections: dict[WebSocket, ConnectionInfo] = {}
        # Heartbeat task
        self._heartbeat_task: asyncio.Task | None = None

    # ── Connection lifecycle ─────────────────────────────────

    async def connect(
        self, ws: WebSocket, user_id: int, username: str, group_ids: list[int],
    ) -> ConnectionInfo:
        """Chấp nhận connection và join vào các rooms."""
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
        """Ngắt kết nối và rời tất cả rooms."""
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

    # ── Join/Leave room dynamically ──────────────────────────

    async def join_room(self, ws: WebSocket, group_id: int) -> None:
        """Thêm connection vào room mới (khi user mở tab nhóm khác)."""
        info = self._connections.get(ws)
        if not info:
            return
        info.group_ids.add(group_id)
        if group_id not in self._rooms:
            self._rooms[group_id] = set()
        self._rooms[group_id].add(info)
        await self._broadcast_presence(group_id)

    async def leave_room(self, ws: WebSocket, group_id: int) -> None:
        """Rời room."""
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

    # ── Broadcasting ─────────────────────────────────────────

    async def broadcast(
        self, group_id: int, event: dict[str, Any], exclude_ws: WebSocket | None = None,
    ) -> int:
        """Broadcast event cho tất cả connections trong room.
        
        Returns: số connections đã gửi thành công.
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

    async def send_to_user(self, user_id: int, event: dict[str, Any]) -> int:
        """Gửi event cho tất cả connections của 1 user."""
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

    # ── Presence ─────────────────────────────────────────────

    async def _broadcast_presence(self, group_id: int) -> None:
        """Broadcast danh sách members online trong room."""
        room = self._rooms.get(group_id, set())
        members = [
            {"user_id": info.user_id, "username": info.username}
            for info in room
        ]
        # Deduplicate by user_id
        seen = {}
        for m in members:
            seen[m["user_id"]] = m
        
        await self.broadcast(group_id, {
            "type": "presence",
            "group_id": group_id,
            "online": list(seen.values()),
            "count": len(seen),
        })

    def get_online_count(self, group_id: int) -> int:
        """Số user online trong room."""
        room = self._rooms.get(group_id, set())
        return len({info.user_id for info in room})

    def get_online_users(self, group_id: int) -> list[dict]:
        """Danh sách user online trong room."""
        room = self._rooms.get(group_id, set())
        seen = {}
        for info in room:
            seen[info.user_id] = {"user_id": info.user_id, "username": info.username}
        return list(seen.values())

    # ── Heartbeat ────────────────────────────────────────────

    async def start_heartbeat(self, interval: int = 30) -> None:
        """Ping tất cả connections mỗi 30s, cleanup dead ones."""
        async def _loop():
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

    # ── Stats ────────────────────────────────────────────────

    @property
    def total_connections(self) -> int:
        return len(self._connections)

    @property
    def total_rooms(self) -> int:
        return len(self._rooms)


# Singleton
ws_manager = WebSocketManager()
```

---

### File mới: `server/routes/ws_routes.py`

```python
"""
server/routes/ws_routes.py — WebSocket endpoint.

Client kết nối: ws://SERVER_IP:8000/ws?token=JWT_TOKEN

Events server → client:
    {"type": "presence",     "group_id": 5, "online": [...], "count": 3}
    {"type": "data_updated", "group_id": 5, "data_type": "customers", "version": 5, "synced_by": "admin"}
    {"type": "member_added", "group_id": 5, "agent_name": "DL Ha Noi"}
    {"type": "member_removed", ...}
    {"type": "ping"}

Events client → server:
    {"type": "pong"}
    {"type": "join_room",  "group_id": 5}
    {"type": "leave_room", "group_id": 5}
"""
from __future__ import annotations

import json
import logging

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from server.config import JWT_SECRET
from server.database import get_db
from server.ws_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()


def _authenticate_ws(token: str) -> dict | None:
    """Xác thực JWT token cho WebSocket. Return user info hoặc None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {
            "user_id": int(payload["sub"]),
            "username": payload["username"],
            "role": payload.get("role", "user"),
        }
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def _get_user_group_ids(user_id: int) -> list[int]:
    """Lấy danh sách group_id mà user liên quan."""
    import psycopg
    from psycopg.rows import dict_row
    from server.config import DB_DSN

    conn = psycopg.connect(DB_DSN, row_factory=dict_row, autocommit=True)
    cur = conn.cursor()

    group_ids = set()

    # Nhóm user sở hữu
    cur.execute(
        "SELECT id FROM groups WHERE owner_id = %s AND deleted_at IS NULL",
        (user_id,),
    )
    for row in cur.fetchall():
        group_ids.add(row["id"])

    # Nhóm có agent của user tham gia
    cur.execute(
        """SELECT DISTINCT a.group_id FROM agents a
           WHERE a.user_id = %s AND a.group_id IS NOT NULL AND a.is_active = TRUE""",
        (user_id,),
    )
    for row in cur.fetchall():
        if row["group_id"]:
            group_ids.add(row["group_id"])

    conn.close()
    return list(group_ids)


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(...)):
    """Main WebSocket endpoint.
    
    Connect: ws://server:8000/ws?token=JWT_TOKEN
    """
    # 1. Authenticate
    user = _authenticate_ws(token)
    if not user:
        await ws.close(code=4001, reason="Invalid token")
        return

    # 2. Get user's group memberships
    group_ids = _get_user_group_ids(user["user_id"])

    # 3. Connect + join rooms
    info = await ws_manager.connect(
        ws, user["user_id"], user["username"], group_ids,
    )

    # 4. Listen for messages
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            if msg_type == "pong":
                info.last_ping = __import__("time").time()

            elif msg_type == "join_room":
                gid = msg.get("group_id")
                if gid and gid in _get_user_group_ids(user["user_id"]):
                    await ws_manager.join_room(ws, gid)

            elif msg_type == "leave_room":
                gid = msg.get("group_id")
                if gid:
                    await ws_manager.leave_room(ws, gid)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WS error for user %s: %s", user["username"], e)
    finally:
        await ws_manager.disconnect(ws)
```

---

### Cập nhật `server/main.py`

```python
# Thêm import:
from server.routes.ws_routes import router as ws_router
from server.ws_manager import ws_manager

# Thêm router:
app.include_router(ws_router)

# Trong lifespan — start heartbeat:
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MaxHub API started.")
    await ws_manager.start_heartbeat(interval=30)   # ← THÊM
    yield
    logger.info("Shutting down.")

# SỬA workers (QUAN TRỌNG):
if __name__ == "__main__":
    from server.database import init_schema
    init_schema()
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, workers=1)  # ← SỬA
```

---

### Cập nhật `server/routes/group_routes.py` — Broadcast khi có thay đổi

```python
# Trong mỗi endpoint thay đổi data nhóm, thêm broadcast:

import asyncio
from server.ws_manager import ws_manager


def _broadcast_sync(group_id: int, event: dict):
    """Helper: broadcast từ sync context (non-async endpoint)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(ws_manager.broadcast(group_id, event))
        else:
            loop.run_until_complete(ws_manager.broadcast(group_id, event))
    except RuntimeError:
        # Không có event loop — skip (sẽ poll lại)
        pass


# Trong add_member():
@router.post("/{group_id}/members")
def add_member(...):
    # ... logic thêm member ...
    
    # Broadcast cho cả nhóm
    _broadcast_sync(group_id, {
        "type": "member_added",
        "group_id": group_id,
        "agent_name": agent["name"],
        "added_by": user["username"],
    })
    return ...


# Trong remove_member():
@router.delete("/{group_id}/members/{agent_id}")
def remove_member(...):
    # ... logic xóa member ...
    
    _broadcast_sync(group_id, {
        "type": "member_removed",
        "group_id": group_id,
        "agent_id": agent_id,
    })
    return ...


# Trong sync endpoint (data update):
@router.post("/{group_id}/sync")
def sync_group_data(...):
    # ... lưu cache ...
    
    _broadcast_sync(group_id, {
        "type": "data_updated",
        "group_id": group_id,
        "data_type": req.data_type,
        "version": new_version,
        "synced_by": user["username"],
        "synced_at": datetime.now(timezone.utc).isoformat(),
    })
    return ...
```

---

## CLIENT-SIDE: PYQT6 WEBSOCKET CLIENT

### File mới: `utils/ws_client.py`

```python
"""
utils/ws_client.py — WebSocket client cho PyQt6.

Dùng QWebSocket (built-in PyQt6) — không cần thêm dependency.

Usage:
    from utils.ws_client import ws_client

    # Kết nối (gọi sau khi login thành công):
    ws_client.connect()

    # Lắng nghe events:
    ws_client.data_updated.connect(self._on_data_updated)
    ws_client.member_added.connect(self._on_member_added)
    ws_client.member_removed.connect(self._on_member_removed)
    ws_client.presence_changed.connect(self._on_presence)

    # Ngắt kết nối (gọi khi logout):
    ws_client.disconnect()
"""
from __future__ import annotations

import json
import logging
from typing import Any

from PyQt6.QtCore import QObject, QUrl, QTimer, pyqtSignal
from PyQt6.QtWebSockets import QWebSocket

logger = logging.getLogger(__name__)


class WsClient(QObject):
    """WebSocket client — auto reconnect, heartbeat, typed signals."""

    # ── Signals ──────────────────────────────────────────────
    connected = pyqtSignal()                    # Kết nối thành công
    disconnected = pyqtSignal()                 # Mất kết nối
    
    # Group events
    data_updated = pyqtSignal(dict)             # {"group_id", "data_type", "version", "synced_by"}
    member_added = pyqtSignal(dict)             # {"group_id", "agent_name", "added_by"}
    member_removed = pyqtSignal(dict)           # {"group_id", "agent_id"}
    presence_changed = pyqtSignal(dict)         # {"group_id", "online": [...], "count"}
    group_updated = pyqtSignal(dict)            # {"group_id", ...}
    permissions_changed = pyqtSignal(dict)      # {"group_id", "agent_id", ...}
    
    # Generic
    message_received = pyqtSignal(dict)         # Mọi message (fallback)

    # ── Config ───────────────────────────────────────────────
    RECONNECT_INTERVALS = [1, 2, 5, 10, 30, 60]  # seconds, escalating backoff
    HEARTBEAT_TIMEOUT = 45  # seconds — nếu không nhận ping trong 45s → reconnect

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._ws = QWebSocket()
        self._ws.connected.connect(self._on_connected)
        self._ws.disconnected.connect(self._on_disconnected)
        self._ws.textMessageReceived.connect(self._on_message)
        self._ws.errorOccurred.connect(self._on_error)

        self._server_url: str = ""
        self._token: str = ""
        self._is_connected = False
        self._should_reconnect = False
        self._reconnect_attempt = 0

        # Reconnect timer
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self._do_reconnect)

        # Heartbeat timeout timer
        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.setInterval(self.HEARTBEAT_TIMEOUT * 1000)
        self._heartbeat_timer.timeout.connect(self._on_heartbeat_timeout)

    # ── Public API ───────────────────────────────────────────

    def connect(self, server_url: str | None = None, token: str | None = None) -> None:
        """Kết nối WebSocket server.
        
        Args:
            server_url: HTTP URL (sẽ tự convert sang ws://)
            token: JWT token
        """
        if server_url:
            self._server_url = server_url
        if token:
            self._token = token

        if not self._server_url or not self._token:
            from utils.api import api
            import os
            from dotenv import load_dotenv
            load_dotenv()
            self._server_url = os.getenv("API_URL", "http://localhost:8000")
            self._token = api.token or ""

        if not self._token:
            logger.warning("WS: No token, skip connect")
            return

        self._should_reconnect = True
        self._reconnect_attempt = 0
        self._do_connect()

    def disconnect(self) -> None:
        """Ngắt kết nối và không reconnect."""
        self._should_reconnect = False
        self._reconnect_timer.stop()
        self._heartbeat_timer.stop()
        if self._ws.isValid():
            self._ws.close()
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def join_room(self, group_id: int) -> None:
        """Join vào room nhóm (khi mở tab nhóm)."""
        self._send({"type": "join_room", "group_id": group_id})

    def leave_room(self, group_id: int) -> None:
        """Rời room nhóm (khi đóng tab nhóm)."""
        self._send({"type": "leave_room", "group_id": group_id})

    # ── Internal ─────────────────────────────────────────────

    def _do_connect(self) -> None:
        """Thực hiện kết nối."""
        # Convert http:// → ws://, https:// → wss://
        ws_url = self._server_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/ws?token={self._token}"

        logger.info("WS connecting to %s...", ws_url.split("?")[0])
        self._ws.open(QUrl(ws_url))

    def _do_reconnect(self) -> None:
        """Reconnect với backoff."""
        if not self._should_reconnect:
            return
        logger.info("WS reconnecting (attempt %d)...", self._reconnect_attempt + 1)
        self._do_connect()

    def _schedule_reconnect(self) -> None:
        """Lên lịch reconnect với escalating backoff."""
        if not self._should_reconnect:
            return
        idx = min(self._reconnect_attempt, len(self.RECONNECT_INTERVALS) - 1)
        delay = self.RECONNECT_INTERVALS[idx] * 1000
        self._reconnect_attempt += 1
        logger.info("WS reconnect in %ds (attempt %d)", delay // 1000, self._reconnect_attempt)
        self._reconnect_timer.start(delay)

    def _send(self, data: dict) -> None:
        """Gửi JSON message."""
        if self._is_connected and self._ws.isValid():
            self._ws.sendTextMessage(json.dumps(data))

    # ── Signal handlers ──────────────────────────────────────

    def _on_connected(self) -> None:
        self._is_connected = True
        self._reconnect_attempt = 0
        self._heartbeat_timer.start()
        logger.info("WS connected!")
        self.connected.emit()

    def _on_disconnected(self) -> None:
        self._is_connected = False
        self._heartbeat_timer.stop()
        logger.info("WS disconnected")
        self.disconnected.emit()
        self._schedule_reconnect()

    def _on_error(self, error) -> None:
        logger.error("WS error: %s", error)
        # QWebSocket sẽ tự emit disconnected sau error

    def _on_heartbeat_timeout(self) -> None:
        """Server không ping trong 45s → connection chết → reconnect."""
        logger.warning("WS heartbeat timeout, reconnecting...")
        self._ws.close()
        # disconnected signal sẽ trigger reconnect

    def _on_message(self, raw: str) -> None:
        """Xử lý message từ server."""
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = msg.get("type", "")

        # Reset heartbeat timer (server còn sống)
        self._heartbeat_timer.start()

        # Route to typed signals
        if msg_type == "ping":
            self._send({"type": "pong"})

        elif msg_type == "data_updated":
            self.data_updated.emit(msg)

        elif msg_type == "member_added":
            self.member_added.emit(msg)

        elif msg_type == "member_removed":
            self.member_removed.emit(msg)

        elif msg_type == "presence":
            self.presence_changed.emit(msg)

        elif msg_type == "group_updated":
            self.group_updated.emit(msg)

        elif msg_type == "permissions_changed":
            self.permissions_changed.emit(msg)

        # Emit generic signal cho tất cả
        self.message_received.emit(msg)


# Singleton
ws_client = WsClient()
```

---

## TÍCH HỢP VÀO APP FLOW

### `main.py` — Connect WS sau login

```python
from utils.ws_client import ws_client

def on_login_success(username: str) -> None:
    login.hide()
    window.show()

    # Sync agents (giữ nguyên)
    from utils.upstream import upstream
    run_in_thread(lambda: upstream.sync_from_db(username))

    # Connect WebSocket (MỚI)
    ws_client.connect()


# Khi logout hoặc đóng app:
def on_logout():
    ws_client.disconnect()
```

### `tabs/group_tab.py` — Lắng nghe realtime events

```python
from utils.ws_client import ws_client

class GroupTab(BaseTab):
    def _build(self, layout):
        # ... build UI ...
        
        # Lắng nghe WebSocket events
        ws_client.data_updated.connect(self._on_ws_data_updated)
        ws_client.member_added.connect(self._on_ws_member_added)
        ws_client.member_removed.connect(self._on_ws_member_removed)
        ws_client.presence_changed.connect(self._on_ws_presence)

    def _on_ws_data_updated(self, event: dict):
        """Có member khác sync data mới → reload cache."""
        if event.get("group_id") == self._current_group_id:
            synced_by = event.get("synced_by", "")
            # Không reload nếu chính mình sync
            if synced_by != api.username:
                self._load_from_cache()
                # Có thể hiện notification: "User X vừa cập nhật dữ liệu"

    def _on_ws_member_added(self, event: dict):
        """Đại lý mới tham gia nhóm → refresh member list."""
        if event.get("group_id") == self._current_group_id:
            self._reload_members()
            # Notification: "Đại lý X vừa tham gia nhóm"

    def _on_ws_member_removed(self, event: dict):
        if event.get("group_id") == self._current_group_id:
            self._reload_members()

    def _on_ws_presence(self, event: dict):
        """Cập nhật indicator online/offline."""
        if event.get("group_id") == self._current_group_id:
            self._update_online_status(event.get("online", []))

    def closeEvent(self, event):
        """Cleanup signals."""
        ws_client.data_updated.disconnect(self._on_ws_data_updated)
        ws_client.member_added.disconnect(self._on_ws_member_added)
        ws_client.member_removed.disconnect(self._on_ws_member_removed)
        ws_client.presence_changed.disconnect(self._on_ws_presence)
        super().closeEvent(event)
```

### `tabs/_upstream_tab.py` — Realtime data update mode nhóm

```python
class UpstreamTab(BaseTab):
    def _build(self, layout):
        # ... build UI hiện tại ...
        
        # WebSocket listener cho mode nhóm
        ws_client.data_updated.connect(self._on_ws_data_updated)

    def _on_ws_data_updated(self, event: dict):
        """Data nhóm được member khác cập nhật → reload."""
        if (self._is_group_mode 
            and event.get("group_id") == self._current_group_id
            and event.get("data_type") == self._data_type
            and event.get("synced_by") != api.username):
            # Load cache mới từ server
            self._load_from_cache()
```

---

## COMPLETE DATA FLOW VỚI WEBSOCKET

```
MEMBER A mở tab nhóm "Team Alpha" (customers):
══════════════════════════════════════════════════════════

A (Client)          Server (WS)         Server (HTTP)       Upstream EE88
│                      │                      │                   │
│──ws connect────────>│                      │                   │
│<─presence(A online)──│                      │                   │
│                      │                      │                   │
│──GET /cache─────────────────────────────────>│                   │
│<─{data, version=3}──────────────────────────│                   │
│ HIỂN THỊ NGAY (từ cache)                    │                   │
│                      │                      │                   │
│ [Cache cũ 5p? → re-fetch]                   │                   │
│──────────────────────fetch agents[1,2,3]───────────────────────>│
│<─────────────────────data từ 3 agents──────────────────────────│
│ CẬP NHẬT HIỂN THỊ    │                      │                   │
│                      │                      │                   │
│──POST /sync(data)───────────────────────────>│                   │
│                      │──version=4            │                   │
│<─{ok, version=4}────────────────────────────│                   │
│                      │                      │                   │
│                      │──broadcast            │                   │
│                      │  data_updated v4      │                   │
│                      │  → all members        │                   │


MEMBER B đang online, nhận broadcast:
══════════════════════════════════════════════════════════

B (Client)          Server (WS)         Server (HTTP)
│                      │                      │
│<─data_updated v4─────│                      │
│   synced_by="A"      │                      │
│                      │                      │
│──GET /cache─────────────────────────────────>│
│<─{data mới, v=4}────────────────────────────│
│ CẬP NHẬT HIỂN THỊ    │                      │
│ (REALTIME ~100ms!)   │                      │
```

---

## EVENTS REFERENCE

### Server → Client

| type | Khi nào | Data |
|------|---------|------|
| `ping` | Mỗi 30s | `{}` |
| `presence` | Member online/offline | `{group_id, online: [{user_id, username}], count}` |
| `data_updated` | Có sync data mới | `{group_id, data_type, version, synced_by, synced_at}` |
| `member_added` | Đại lý mới join | `{group_id, agent_name, added_by}` |
| `member_removed` | Đại lý bị xóa/rời | `{group_id, agent_id}` |
| `group_updated` | Sửa tên/mô tả nhóm | `{group_id, name, description}` |
| `permissions_changed` | Đổi quyền member | `{group_id, agent_id, permissions}` |

### Client → Server

| type | Khi nào | Data |
|------|---------|------|
| `pong` | Phản hồi ping | `{}` |
| `join_room` | Mở tab nhóm | `{group_id}` |
| `leave_room` | Đóng tab nhóm | `{group_id}` |

---

## CHECKLIST TRIỂN KHAI

```
Server:
  [ ] Sửa workers=1 trong main.py và systemd service
  [ ] Tạo server/ws_manager.py
  [ ] Tạo server/routes/ws_routes.py
  [ ] Include ws_router trong main.py
  [ ] Start heartbeat trong lifespan
  [ ] Thêm broadcast calls trong group_routes.py (add/remove member)
  [ ] Thêm broadcast calls trong sync endpoint (data_updated)
  [ ] Test: 2 clients cùng connect, broadcast hoạt động

Client:
  [ ] Tạo utils/ws_client.py (QWebSocket + auto reconnect)
  [ ] Connect WS trong main.py sau login
  [ ] Disconnect WS khi logout
  [ ] GroupTab: listen data_updated, member_added/removed, presence
  [ ] UpstreamTab: listen data_updated cho mode nhóm
  [ ] AccountTab: listen member_added (đại lý được thêm vào nhóm)
  [ ] UI: indicator "● online" cho members
  [ ] Test: mất mạng → reconnect tự động

Production:
  [ ] Systemd service: sửa --workers 1
  [ ] Nginx reverse proxy: thêm WebSocket upgrade headers
  [ ] Monitor: log số connections, broadcast latency
```

### Nginx config cho WebSocket (nếu dùng):

```nginx
location /ws {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;  # 24h — giữ connection sống
}
```
