"""
run_tests.py — Chạy test suite.

Dùng:
    python run_tests.py                  # Tất cả tests
    python run_tests.py --unit           # Chỉ unit tests
    python run_tests.py --integration    # Chỉ integration tests
    python run_tests.py --ui             # Chỉ UI tests
    python run_tests.py --performance    # Chỉ performance tests
    python run_tests.py --coverage       # Với coverage report
    python run_tests.py --fast           # Bỏ qua slow tests

Exit code: 0 = pass, 1 = failures
"""
import sys
import subprocess


def main() -> int:
    args = sys.argv[1:]

    cmd = [sys.executable, "-m", "pytest"]

    if "--unit" in args:
        cmd.extend(["-m", "unit"])
        cmd.append("tests/unit/")
    elif "--integration" in args:
        cmd.extend(["-m", "integration"])
        cmd.append("tests/integration/")
    elif "--ui" in args:
        cmd.extend(["-m", "ui"])
        cmd.append("tests/ui/")
    elif "--performance" in args:
        cmd.extend(["-m", "performance"])
        cmd.append("tests/performance/")
    elif "--fast" in args:
        cmd.extend(["-m", "not slow and not performance"])

    if "--coverage" in args:
        cmd.extend([
            "--cov=utils",
            "--cov=server",
            "--cov=core",
            "--cov-report=term-missing",
            "--cov-report=html:reports/coverage",
        ])

    # Always verbose and short traceback
    cmd.extend(["-v", "--tb=short"])

    print(f"Running: {' '.join(cmd)}")
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
