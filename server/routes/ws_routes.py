"""
server/routes/ws_routes.py — WebSocket endpoint.

Client ket noi: ws://SERVER_IP:8000/ws?token=JWT_TOKEN

Events server -> client:
    {"type": "presence",     "group_id": 5, "online": [...], "count": 3}
    {"type": "data_updated", "group_id": 5, "data_type": "customers", "version": 5}
    {"type": "member_added", "group_id": 5, "agent_name": "DL Ha Noi"}
    {"type": "member_removed", ...}
    {"type": "ping"}

Events client -> server:
    {"type": "pong"}
    {"type": "join_room",  "group_id": 5}
    {"type": "leave_room", "group_id": 5}
"""
from __future__ import annotations

import json
import logging
import time

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from server.config import JWT_SECRET, DB_DSN
from server.ws_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()


def _authenticate_ws(token: str) -> dict | None:
    """Xac thuc JWT token cho WebSocket. Return user info hoac None."""
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
    """Lay danh sach group_id ma user lien quan."""
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(DB_DSN, row_factory=dict_row, autocommit=True)
    cur = conn.cursor()

    group_ids: set[int] = set()

    # Nhom user so huu
    cur.execute(
        "SELECT id FROM groups WHERE owner_id = %s AND deleted_at IS NULL",
        (user_id,),
    )
    for row in cur.fetchall():
        group_ids.add(row["id"])

    # Nhom co agent cua user tham gia
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
                info.last_ping = time.time()

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
