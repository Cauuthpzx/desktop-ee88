"""
monitoring/metrics.py — Performance metrics collection.

Timing decorator cho critical functions + metrics storage.

Dùng:
    from monitoring.metrics import track_performance, get_metrics

    @track_performance
    def load_data():
        ...
    # Auto log: "load_data completed in 0.234s"

    # Xem metrics:
    stats = get_metrics("load_data")
    # {"count": 42, "avg_ms": 234, "min_ms": 100, "max_ms": 500, "p95_ms": 450}
"""
from __future__ import annotations

import functools
import logging
import threading
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

# Thread-safe metrics storage
_lock = threading.Lock()
_metrics: dict[str, list[float]] = defaultdict(list)
_MAX_SAMPLES = 1000  # Giữ tối đa 1000 samples mỗi function


def track_performance(fn=None, *, name: str | None = None):
    """Decorator đo execution time.

    Dùng:
        @track_performance
        def my_func(): ...

        @track_performance(name="custom_name")
        def my_func(): ...
    """
    def decorator(func):
        metric_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                _record(metric_name, elapsed_ms)
                if elapsed_ms > 1000:
                    logger.warning("%s took %.0fms", metric_name, elapsed_ms)
                else:
                    logger.debug("%s completed in %.1fms", metric_name, elapsed_ms)

        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


def _record(name: str, elapsed_ms: float) -> None:
    """Ghi nhận 1 sample."""
    with _lock:
        samples = _metrics[name]
        samples.append(elapsed_ms)
        if len(samples) > _MAX_SAMPLES:
            # Giữ nửa sau (mới nhất)
            _metrics[name] = samples[_MAX_SAMPLES // 2:]


def record_metric(name: str, value_ms: float) -> None:
    """Ghi nhận metric thủ công (không qua decorator)."""
    _record(name, value_ms)


def get_metrics(name: str) -> dict | None:
    """Lấy thống kê cho 1 metric."""
    with _lock:
        samples = list(_metrics.get(name, []))
    if not samples:
        return None

    samples_sorted = sorted(samples)
    n = len(samples_sorted)
    return {
        "count": n,
        "avg_ms": round(sum(samples) / n, 1),
        "min_ms": round(samples_sorted[0], 1),
        "max_ms": round(samples_sorted[-1], 1),
        "p50_ms": round(samples_sorted[n // 2], 1),
        "p95_ms": round(samples_sorted[int(n * 0.95)], 1) if n >= 20 else None,
        "p99_ms": round(samples_sorted[int(n * 0.99)], 1) if n >= 100 else None,
    }


def get_all_metrics() -> dict[str, dict]:
    """Lấy thống kê tất cả metrics."""
    with _lock:
        names = list(_metrics.keys())
    return {name: get_metrics(name) for name in names if get_metrics(name)}


def clear_metrics() -> None:
    """Xóa tất cả metrics data."""
    with _lock:
        _metrics.clear()


def export_metrics_json() -> str:
    """Export tất cả metrics dạng JSON."""
    import json
    return json.dumps(get_all_metrics(), indent=2)
