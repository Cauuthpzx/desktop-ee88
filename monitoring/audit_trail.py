"""
monitoring/audit_trail.py — Ghi lại hành động user (opt-in, local only).

Privacy-respecting:
- KHÔNG log nội dung user nhập
- KHÔNG log file paths đầy đủ
- KHÔNG log personal data
- Chỉ log action names và timestamps
- User có thể tắt hoàn toàn
- User có thể xem/xóa audit log

Dùng:
    from monitoring.audit_trail import AuditTrail

    trail = AuditTrail(enabled=True)
    trail.log("button_click", "export_data")
    trail.log("tab_switch", "settings")

    # Xem log:
    entries = trail.get_recent(limit=50)

    # Xóa:
    trail.clear()
"""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_AUDIT_DIR = Path(os.path.expanduser("~")) / ".maxhub" / "audit"
_MAX_ENTRIES = 5000  # Giữ tối đa 5000 entries
_LOG_FILE = "audit_trail.jsonl"


class AuditTrail:
    """Ghi lại user actions — opt-in, local only."""

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._lock = threading.Lock()
        _AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        self._filepath = _AUDIT_DIR / _LOG_FILE

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def log(self, category: str, action: str, details: str = "") -> None:
        """Ghi 1 action vào audit trail.

        Args:
            category: Loại action (button_click, tab_switch, feature_use, error)
            action: Tên action cụ thể (export_data, login, change_theme)
            details: Thông tin thêm (không chứa PII)
        """
        if not self._enabled:
            return

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "cat": category,
            "act": action,
        }
        if details:
            entry["det"] = details

        with self._lock:
            try:
                with open(self._filepath, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except OSError as e:
                logger.debug("Audit trail write failed: %s", e)

    def get_recent(self, limit: int = 50) -> list[dict]:
        """Đọc N entries gần nhất."""
        with self._lock:
            try:
                lines = self._filepath.read_text(encoding="utf-8").splitlines()
                entries = []
                for line in lines[-limit:]:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                return entries
            except OSError:
                return []

    def get_stats(self) -> dict:
        """Thống kê action frequency."""
        entries = self.get_recent(limit=_MAX_ENTRIES)
        stats: dict[str, int] = {}
        for e in entries:
            key = f"{e.get('cat', '?')}.{e.get('act', '?')}"
            stats[key] = stats.get(key, 0) + 1
        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

    def clear(self) -> None:
        """Xóa toàn bộ audit trail."""
        with self._lock:
            try:
                self._filepath.unlink(missing_ok=True)
            except OSError:
                pass

    def trim(self) -> None:
        """Giữ chỉ _MAX_ENTRIES entries mới nhất."""
        with self._lock:
            try:
                lines = self._filepath.read_text(encoding="utf-8").splitlines()
                if len(lines) > _MAX_ENTRIES:
                    keep = lines[-_MAX_ENTRIES:]
                    self._filepath.write_text("\n".join(keep) + "\n", encoding="utf-8")
            except OSError:
                pass
