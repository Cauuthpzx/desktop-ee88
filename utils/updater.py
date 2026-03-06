"""
utils/updater.py
Auto update — check for new version, download with integrity verification, apply update.

Flow:
    1. check_update()     — call API, compare versions → returns update info or None
    2. download_update()  — download file + verify SHA-256 hash → returns local path
    3. apply_update()     — save session, create updater script, quit + restart

Usage:
    from utils.updater import check_update, download_update, apply_update, APP_VERSION
"""
from __future__ import annotations

import hashlib
import logging
import os
import sys
import subprocess
import tempfile
import urllib.request

from utils.api import api

logger = logging.getLogger(__name__)

# Version hien tai — tang moi khi release
APP_VERSION = "1.0.0"


def _parse_version(v: str) -> tuple[int, ...]:
    """'1.2.3' → (1, 2, 3)"""
    return tuple(int(x) for x in v.strip().split("."))


def check_update() -> dict | None:
    """
    Call /api/version. Return update info dict if newer version available, else None.
    Run in worker thread.

    Expected server response:
        {
            "version": "1.1.0",
            "update_url": "https://example.com/MaxHub_1.1.0.exe",
            "sha256": "abc123...",    # optional but recommended
            "changelog": "- Fix ...", # optional
            "force": false,           # optional — force update
            "min_version": "0.9.0"    # optional — minimum version for this update
        }
    """
    ok, data = api.get("/api/version", auth=False, timeout=10)
    if not ok:
        return None

    server_ver = data.get("version", "0.0.0")
    update_url = data.get("update_url", "")

    try:
        if _parse_version(server_ver) > _parse_version(APP_VERSION):
            # Check min_version — if current version is too old, force update
            min_ver = data.get("min_version")
            force = data.get("force", False)
            if min_ver:
                try:
                    if _parse_version(APP_VERSION) < _parse_version(min_ver):
                        force = True
                except (ValueError, TypeError):
                    pass

            return {
                "version": server_ver,
                "update_url": update_url,
                "sha256": data.get("sha256", ""),
                "changelog": data.get("changelog", ""),
                "force": force,
                "file_size": data.get("file_size", 0),
            }
    except (ValueError, TypeError):
        logger.warning("Invalid version format: %s", server_ver)

    return None


def download_update(
    url: str,
    expected_sha256: str = "",
    progress_callback=None,
    cancel_flag: list | None = None,
) -> str:
    """
    Download update file to %TEMP%, verify SHA-256 if provided.
    Run in worker thread.

    Args:
        url: Download URL
        expected_sha256: Expected SHA-256 hash (hex). Skip verification if empty.
        progress_callback: Callable(int) — progress 0-100
        cancel_flag: list[bool] — set cancel_flag[0] = True to cancel download

    Returns:
        Path to downloaded file.

    Raises:
        RuntimeError: If cancelled, hash mismatch, or download error.
    """
    tmp_dir = tempfile.mkdtemp(prefix="maxhub_update_")
    filename = url.rsplit("/", 1)[-1] or "MaxHub_update.exe"
    dest = os.path.join(tmp_dir, filename)

    req = urllib.request.Request(url, headers={
        "User-Agent": f"MaxHub/{APP_VERSION}",
    })

    hasher = hashlib.sha256()

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 64 * 1024  # 64KB

            with open(dest, "wb") as f:
                while True:
                    # Check cancel
                    if cancel_flag and cancel_flag[0]:
                        raise RuntimeError("CANCELLED")

                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    hasher.update(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        progress_callback(int(downloaded * 100 / total))
    except RuntimeError:
        # Clean up partial download
        _cleanup_file(dest)
        raise
    except Exception as e:
        _cleanup_file(dest)
        raise RuntimeError(f"Download failed: {e}") from e

    # Verify SHA-256
    if expected_sha256:
        actual = hasher.hexdigest()
        if actual.lower() != expected_sha256.lower():
            _cleanup_file(dest)
            raise RuntimeError(
                f"Hash mismatch — file may be corrupted or tampered.\n"
                f"Expected: {expected_sha256[:16]}...\n"
                f"Got: {actual[:16]}..."
            )
        logger.info("SHA-256 verified OK: %s", actual[:16])

    logger.info("Update downloaded: %s (%d bytes)", dest, downloaded)
    return dest


def apply_update(exe_path: str) -> None:
    """
    Save session, create updater script, quit app, script replaces file and restarts.
    Call in MAIN THREAD (needs to quit app).
    """
    # Save JWT token before quitting
    api.save_session()

    current_exe = sys.executable
    is_frozen = getattr(sys, "frozen", False)

    if is_frozen:
        # Frozen .exe — create PowerShell script for reliable replacement
        ps_path = os.path.join(tempfile.gettempdir(), "maxhub_update.ps1")
        ps_content = f"""
# MaxHub Auto-Updater
$ErrorActionPreference = "Stop"
$source = "{exe_path}"
$target = "{current_exe}"
$maxWait = 30  # seconds

# Wait for the old process to exit
$processName = [System.IO.Path]::GetFileNameWithoutExtension($target)
$waited = 0
while ($waited -lt $maxWait) {{
    $proc = Get-Process -Name $processName -ErrorAction SilentlyContinue
    if (-not $proc) {{ break }}
    Start-Sleep -Seconds 1
    $waited++
}}

# Backup old exe
$backup = "$target.bak"
if (Test-Path $target) {{
    Copy-Item $target $backup -Force
}}

# Replace
try {{
    Copy-Item $source $target -Force
    Remove-Item $source -Force -ErrorAction SilentlyContinue
    Remove-Item $backup -Force -ErrorAction SilentlyContinue
    Start-Process $target
}} catch {{
    # Rollback on failure
    if (Test-Path $backup) {{
        Copy-Item $backup $target -Force
        Remove-Item $backup -Force -ErrorAction SilentlyContinue
    }}
    Start-Process $target
}}

# Self-delete
Remove-Item $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
"""
        with open(ps_path, "w", encoding="utf-8") as f:
            f.write(ps_content)

        subprocess.Popen(
            [
                "powershell", "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-File", ps_path,
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        # Running from source — just log
        logger.info(
            "Update downloaded to: %s (source mode — manual install)", exe_path
        )
        return

    # Quit app
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app:
        app.quit()


def _cleanup_file(path: str) -> None:
    """Remove file and parent temp dir silently."""
    try:
        if os.path.exists(path):
            os.remove(path)
        parent = os.path.dirname(path)
        if parent and os.path.isdir(parent) and parent.startswith(tempfile.gettempdir()):
            os.rmdir(parent)
    except OSError:
        pass
