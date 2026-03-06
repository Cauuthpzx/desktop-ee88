"""
server/routes/system_routes.py — Health check, version/update info.
"""
from fastapi import APIRouter

from server.config import (
    APP_VERSION, UPDATE_URL, UPDATE_SHA256,
    UPDATE_CHANGELOG, UPDATE_FORCE, UPDATE_FILE_SIZE,
)

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health():
    return {"ok": True, "service": "maxhub-api"}


@router.get("/version")
def version():
    return {
        "version": APP_VERSION,
        "update_url": UPDATE_URL,
        "sha256": UPDATE_SHA256,
        "changelog": UPDATE_CHANGELOG,
        "force": UPDATE_FORCE,
        "file_size": UPDATE_FILE_SIZE,
    }
