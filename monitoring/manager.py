"""
monitoring/manager.py — MonitoringManager tổng hợp.

Quản lý tất cả monitoring services:
- CrashReporter
- HealthChecker
- Metrics (module-level, không cần start/stop)
- AuditTrail

Dùng:
    from monitoring import MonitoringManager

    monitor = MonitoringManager(app_version="1.0.0")
    monitor.start()
    # ...
    monitor.shutdown()

Config qua constructor hoặc settings:
    monitor = MonitoringManager(
        app_version="1.0.0",
        enable_health=True,
        enable_audit=True,
        health_interval=60,
    )
"""
from __future__ import annotations

import logging

from monitoring.crash_reporter import CrashReporter
from monitoring.health_checker import HealthChecker
from monitoring.audit_trail import AuditTrail

logger = logging.getLogger(__name__)


class MonitoringManager:
    """Quản lý tập trung tất cả monitoring services."""

    def __init__(
        self,
        app_version: str = "1.0.0",
        enable_crash: bool = True,
        enable_health: bool = True,
        enable_audit: bool = True,
        health_interval: int = 60,
    ) -> None:
        self._app_version = app_version

        self.crash_reporter = CrashReporter(app_version) if enable_crash else None
        self.health_checker = HealthChecker(interval_sec=health_interval) if enable_health else None
        self.audit_trail = AuditTrail(enabled=enable_audit) if enable_audit else None

        self._started = False

    def start(self) -> None:
        """Bật tất cả monitoring services."""
        if self._started:
            return

        try:
            if self.crash_reporter:
                self.crash_reporter.install()

            if self.health_checker:
                self.health_checker.start()
        except Exception:
            # Rollback on partial failure
            if self.health_checker:
                self.health_checker.stop()
            if self.crash_reporter:
                self.crash_reporter.uninstall()
            raise

        self._started = True
        logger.info(
            "Monitoring started (crash=%s, health=%s, audit=%s)",
            self.crash_reporter is not None,
            self.health_checker is not None,
            self.audit_trail is not None,
        )

    def shutdown(self) -> None:
        """Tắt tất cả monitoring services."""
        if not self._started:
            return

        if self.health_checker:
            self.health_checker.stop()

        if self.crash_reporter:
            self.crash_reporter.uninstall()

        self._started = False
        logger.info("Monitoring shutdown complete")

    def log_action(self, category: str, action: str, details: str = "") -> None:
        """Shortcut: ghi audit trail + crash reporter action."""
        if self.audit_trail:
            self.audit_trail.log(category, action, details)
        if self.crash_reporter:
            self.crash_reporter.log_action(f"{category}: {action}")

    @property
    def is_running(self) -> bool:
        return self._started
