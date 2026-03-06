"""
utils/updater.py
Auto update — kiem tra version moi va cap nhat app.

Dung:
    from utils.updater import check_update, do_update, APP_VERSION

    # Kiem tra (chay trong worker thread)
    info = check_update()
    if info:  # co ban moi
        do_update(info["update_url"])  # tai + restart
"""
from __future__ import annotations

import logging
import os
import sys
import subprocess
import tempfile
import urllib.request

from utils.api import api

logger = logging.getLogger(__name__)

# Version hien tai cua app — tang moi khi release
APP_VERSION = "1.0.0"


def _parse_version(v: str) -> tuple[int, ...]:
    """'1.2.3' → (1, 2, 3)"""
    return tuple(int(x) for x in v.strip().split("."))


def check_update() -> dict | None:
    """
    Goi /api/version. Tra ve dict neu co ban moi, None neu khong.
    Goi trong worker thread.
    """
    ok, data = api.get("/api/version", auth=False, timeout=10)
    if not ok:
        return None

    server_ver = data.get("version", "0.0.0")
    update_url = data.get("update_url", "")
    force = data.get("force", False)

    try:
        if _parse_version(server_ver) > _parse_version(APP_VERSION):
            return {
                "version": server_ver,
                "update_url": update_url,
                "force": force,
            }
    except (ValueError, TypeError):
        logger.warning("Invalid version format: %s", server_ver)

    return None


def download_update(url: str, progress_callback=None) -> str:
    """
    Tai file update ve %TEMP%. Tra ve duong dan file da tai.
    Goi trong worker thread.
    """
    tmp_dir = tempfile.mkdtemp(prefix="maxhub_update_")
    filename = url.rsplit("/", 1)[-1] or "MaxHub_update.exe"
    dest = os.path.join(tmp_dir, filename)

    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=120)
    total = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    chunk_size = 64 * 1024  # 64KB

    with open(dest, "wb") as f:
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if progress_callback and total > 0:
                progress_callback(int(downloaded * 100 / total))

    logger.info("Update downloaded: %s (%d bytes)", dest, downloaded)
    return dest


def apply_update(exe_path: str) -> None:
    """
    Luu session, tao updater script, thoat app, script thay file va restart.
    Goi trong MAIN THREAD (vi can thoat app).
    """
    # Luu JWT token truoc khi thoat
    api.save_session()

    current_exe = sys.executable
    # Neu dang chay tu source (python main.py), khong tu thay duoc
    is_frozen = getattr(sys, "frozen", False)

    if is_frozen:
        # App dong goi .exe — tao .bat de thay file
        bat_path = os.path.join(tempfile.gettempdir(), "maxhub_update.bat")
        bat_content = f"""@echo off
echo Dang cap nhat MaxHub...
timeout /t 2 /nobreak >nul
copy /y "{exe_path}" "{current_exe}"
del "{exe_path}"
start "" "{current_exe}"
del "%~f0"
"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        # Dang chay tu source — chi thong bao
        logger.info("Update downloaded to: %s (source mode — manual install)", exe_path)
        return

    # Thoat app
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app:
        app.quit()
