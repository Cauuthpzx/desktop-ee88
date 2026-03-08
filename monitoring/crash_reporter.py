"""
monitoring/crash_reporter.py — Global exception handler + crash report.

Bắt mọi unhandled exception, lưu crash report vào file local.
KHÔNG tự động gửi network — chỉ lưu local.

Dùng:
    from monitoring.crash_reporter import CrashReporter

    reporter = CrashReporter()
    reporter.install()       # Đăng ký sys.excepthook
    reporter.uninstall()     # Khôi phục excepthook cũ

    # Kiểm tra crash từ session trước:
    last = reporter.get_last_crash()
    if last:
        print(f"Last crash: {last['timestamp']}")
"""
from __future__ import annotations

import logging
import os
import platform
import sys
import traceback
import json
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Thư mục lưu crash reports
_CRASHES_DIR = Path(os.path.expanduser("~")) / ".maxhub" / "crashes"
_MAX_REPORTS = 20  # Giữ tối đa 20 file crash


class CrashReporter:
    """Bắt unhandled exceptions, lưu crash report."""

    def __init__(self, app_version: str = "1.0.0") -> None:
        self._app_version = app_version
        self._original_hook = None
        self._recent_actions: list[str] = []
        self._max_actions = 20
        _CRASHES_DIR.mkdir(parents=True, exist_ok=True)

    def install(self) -> None:
        """Đăng ký global exception hook."""
        if self._original_hook is not None:
            return  # Already installed
        self._original_hook = sys.excepthook
        sys.excepthook = self._handle_exception
        logger.info("Crash reporter installed")

    def uninstall(self) -> None:
        """Khôi phục exception hook cũ."""
        if self._original_hook:
            sys.excepthook = self._original_hook
            self._original_hook = None

    def log_action(self, action: str) -> None:
        """Ghi lại action gần đây (cho crash report context)."""
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {action}"
        self._recent_actions.append(entry)
        if len(self._recent_actions) > self._max_actions:
            self._recent_actions.pop(0)

    def _handle_exception(self, exc_type, exc_value, exc_tb) -> None:
        """Global exception handler — lưu crash report."""
        try:
            report = self._build_report(exc_type, exc_value, exc_tb)
            filepath = self._save_report(report)
            logger.critical("CRASH: %s saved to %s", exc_value, filepath)
        except Exception as save_err:
            logger.error("Failed to save crash report: %s", save_err)

        # Gọi original hook (nếu có) để print traceback bình thường
        if self._original_hook:
            self._original_hook(exc_type, exc_value, exc_tb)

    def _build_report(self, exc_type, exc_value, exc_tb) -> dict:
        """Tạo crash report dict."""
        mem = {"rss_mb": 0, "vms_mb": 0}
        try:
            import psutil  # lazy import — optional dependency

            proc = psutil.Process(os.getpid())
            mem_info = proc.memory_info()
            mem = {
                "rss_mb": round(mem_info.rss / 1024 / 1024, 1),
                "vms_mb": round(mem_info.vms / 1024 / 1024, 1),
            }
        except Exception:
            pass

        return {
            "app_version": self._app_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "os": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "memory": mem,
            "exception_type": exc_type.__name__ if exc_type else "Unknown",
            "exception_message": str(exc_value),
            "traceback": traceback.format_exception(exc_type, exc_value, exc_tb),
            "recent_actions": list(self._recent_actions),
        }

    def _save_report(self, report: dict) -> Path:
        """Lưu crash report vào file JSON."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = _CRASHES_DIR / f"crash_{ts}.json"
        filepath.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        self._cleanup_old_reports()
        return filepath

    def _cleanup_old_reports(self) -> None:
        """Xóa crash reports cũ, giữ tối đa _MAX_REPORTS."""
        reports = sorted(_CRASHES_DIR.glob("crash_*.json"), key=lambda p: p.stat().st_mtime)
        while len(reports) > _MAX_REPORTS:
            reports.pop(0).unlink(missing_ok=True)

    def get_last_crash(self) -> dict | None:
        """Đọc crash report gần nhất. None nếu không có."""
        reports = sorted(_CRASHES_DIR.glob("crash_*.json"), key=lambda p: p.stat().st_mtime)
        if not reports:
            return None
        try:
            return json.loads(reports[-1].read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def get_all_crashes(self) -> list[dict]:
        """Đọc tất cả crash reports."""
        result = []
        for f in sorted(_CRASHES_DIR.glob("crash_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                result.append(json.loads(f.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return result

    def clear_crashes(self) -> int:
        """Xóa tất cả crash reports. Trả về số file đã xóa."""
        count = 0
        for f in _CRASHES_DIR.glob("crash_*.json"):
            try:
                f.unlink()
                count += 1
            except OSError:
                pass
        return count
