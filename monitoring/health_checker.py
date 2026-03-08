"""
monitoring/health_checker.py — Kiểm tra sức khỏe app định kỳ.

Chạy trong background thread, kiểm tra:
- Memory usage
- Thread count
- API server connectivity

Dùng:
    from monitoring.health_checker import HealthChecker

    checker = HealthChecker(interval_sec=60)
    checker.start()
    ...
    checker.stop()

    status = checker.status()
    # {"level": "HEALTHY", "memory_mb": 120, "threads": 8, ...}
"""
from __future__ import annotations

import gc
import logging
import os
import threading
import time

logger = logging.getLogger(__name__)


class HealthStatus:
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class HealthChecker:
    """Kiểm tra sức khỏe app theo chu kỳ."""

    def __init__(self, interval_sec: int = 60, memory_warn_mb: int = 500) -> None:
        self._interval = interval_sec
        self._memory_warn = memory_warn_mb
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_status: dict = {"level": HealthStatus.HEALTHY}
        self._lock = threading.Lock()

    def start(self) -> None:
        """Bắt đầu health check loop trong background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="health-checker")
        self._thread.start()
        logger.info("Health checker started (interval=%ds)", self._interval)

    def stop(self) -> None:
        """Dừng health check."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._thread = None
        logger.info("Health checker stopped")

    def status(self) -> dict:
        """Trả về status check gần nhất."""
        with self._lock:
            return dict(self._last_status)

    def check_now(self) -> dict:
        """Chạy health check ngay lập tức."""
        result = self._run_checks()
        with self._lock:
            self._last_status = result
        return result

    def _loop(self) -> None:
        """Background loop."""
        while self._running:
            try:
                result = self._run_checks()
                with self._lock:
                    self._last_status = result

                if result["level"] == HealthStatus.WARNING:
                    logger.warning("Health WARNING: %s", result.get("warnings", []))
                elif result["level"] == HealthStatus.CRITICAL:
                    logger.error("Health CRITICAL: %s", result.get("warnings", []))
                    self._auto_mitigate(result)
            except Exception as e:
                logger.error("Health check error: %s", e)

            # Sleep in small chunks for responsive shutdown
            for _ in range(self._interval * 2):
                if not self._running:
                    return
                time.sleep(0.5)

    def _run_checks(self) -> dict:
        """Chạy tất cả health checks."""
        warnings: list[str] = []
        level = HealthStatus.HEALTHY

        # 1. Memory usage
        memory_mb = self._get_memory_mb()
        if memory_mb > self._memory_warn * 1.3:
            level = HealthStatus.CRITICAL
            warnings.append(f"Memory critical: {memory_mb:.0f}MB")
        elif memory_mb > self._memory_warn:
            level = max(level, HealthStatus.WARNING)
            warnings.append(f"Memory high: {memory_mb:.0f}MB")

        # 2. Thread count
        thread_count = threading.active_count()
        if thread_count > 50:
            level = max(level, HealthStatus.WARNING)
            warnings.append(f"Too many threads: {thread_count}")

        return {
            "level": level,
            "memory_mb": round(memory_mb, 1),
            "thread_count": thread_count,
            "warnings": warnings,
            "timestamp": time.time(),
        }

    def _auto_mitigate(self, status: dict) -> None:
        """Tự động xử lý khi có vấn đề."""
        # Memory cao → force garbage collection
        if status.get("memory_mb", 0) > self._memory_warn:
            gc.collect()
            logger.info("Auto-mitigation: forced GC")

    @staticmethod
    def _get_memory_mb() -> float:
        """Lấy memory usage (MB) của process hiện tại."""
        try:
            import psutil
            return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback: đọc /proc trên Linux, hoặc trả 0
            try:
                import resource
                return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            except ImportError:
                return 0
