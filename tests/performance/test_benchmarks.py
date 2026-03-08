"""
Performance tests — đo thời gian và memory cho critical paths.
"""
import time
import pytest


@pytest.fixture(autouse=True)
def _init_i18n():
    from core.i18n import init
    init()


@pytest.mark.performance
class TestValidatorPerformance:
    def test_validate_all_10000_items(self):
        """validate_all phải xử lý 10k items dưới 50ms."""
        from utils.validators import validate_all
        items = [None if i % 2 == 0 else f"Error {i}" for i in range(10000)]
        start = time.perf_counter()
        result = validate_all(items)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.05, f"validate_all took {elapsed:.3f}s (limit 50ms)"
        assert len(result) == 5000


@pytest.mark.performance
class TestFormatterPerformance:
    def test_currency_format_10000_items(self):
        """currency() phải format 10k items dưới 100ms."""
        from utils.formatters import currency
        values = list(range(10000))
        start = time.perf_counter()
        results = [currency(v) for v in values]
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, f"currency format took {elapsed:.3f}s (limit 100ms)"
        assert len(results) == 10000

    def test_truncate_performance(self):
        from utils.formatters import truncate
        long_text = "A" * 10000
        start = time.perf_counter()
        for _ in range(10000):
            truncate(long_text, 100)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, f"truncate took {elapsed:.3f}s"


@pytest.mark.performance
class TestI18nPerformance:
    def test_translation_lookup_speed(self):
        """t() phải tra cứu key dưới 1ms trung bình."""
        from core.i18n import t
        keys = ["login.title", "crud.add", "dialog.confirm", "validator.required"]
        start = time.perf_counter()
        for _ in range(10000):
            for key in keys:
                t(key)
        elapsed = time.perf_counter() - start
        avg_us = (elapsed / 40000) * 1_000_000
        assert avg_us < 100, f"t() avg {avg_us:.1f}µs (limit 100µs)"


@pytest.mark.performance
class TestJWTPerformance:
    def test_token_create_decode_speed(self):
        """Create + decode JWT dưới 5ms mỗi lần."""
        from server.auth import create_token, decode_token
        start = time.perf_counter()
        for i in range(1000):
            token = create_token(i, f"user{i}", "user", 0)
            decode_token(token)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 1000) * 1000
        assert avg_ms < 5, f"JWT create+decode avg {avg_ms:.2f}ms (limit 5ms)"


@pytest.mark.performance
class TestMemoryUsage:
    def test_no_memory_leak_in_validators(self):
        """Chạy validators nhiều lần không tăng memory đáng kể."""
        import tracemalloc
        from utils.validators import validate_all, required, email

        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        for _ in range(10000):
            validate_all([
                required("Name", "Alice"),
                email("Email", "alice@example.com"),
            ])

        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, "lineno")

        # Tổng memory tăng không quá 1MB
        total_diff = sum(s.size_diff for s in stats if s.size_diff > 0)
        assert total_diff < 1_000_000, f"Memory grew {total_diff / 1024:.1f}KB"
        tracemalloc.stop()
