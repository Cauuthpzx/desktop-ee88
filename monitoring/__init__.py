"""
monitoring/ — Hệ thống giám sát app.

Modules:
    - crash_reporter: Bắt unhandled exceptions, lưu crash report
    - health_checker: Kiểm tra sức khỏe app định kỳ
    - metrics: Đo performance các function quan trọng
    - audit_trail: Ghi lại hành động user (opt-in, local only)

Dùng:
    from monitoring import MonitoringManager

    monitor = MonitoringManager()
    monitor.start()          # Bật tất cả services
    ...
    monitor.shutdown()       # Tắt khi app đóng

Tích hợp vào main.py:
    monitor = MonitoringManager()
    monitor.start()
    app.aboutToQuit.connect(monitor.shutdown)
"""
from monitoring.manager import MonitoringManager

__all__ = ["MonitoringManager"]
