# Makefile — Quick commands cho development

.PHONY: test test-unit test-integration test-ui test-perf test-fast coverage install-dev lint

# ── Testing ──────────────────────────────────────────────────
test:
	python -m pytest tests/ -v --tb=short

test-unit:
	python -m pytest tests/unit/ -v --tb=short

test-integration:
	python -m pytest tests/integration/ -v --tb=short -m integration

test-ui:
	python -m pytest tests/ui/ -v --tb=short -m ui

test-perf:
	python -m pytest tests/performance/ -v --tb=short -m performance

test-fast:
	python -m pytest tests/ -v --tb=short -m "not slow and not performance"

coverage:
	python -m pytest tests/ -v --tb=short --cov=utils --cov=server --cov=core --cov-report=term-missing --cov-report=html:reports/coverage

# ── Setup ────────────────────────────────────────────────────
install-dev:
	pip install -r requirements-dev.txt

# ── Server ───────────────────────────────────────────────────
server:
	python -m uvicorn server.main:app --reload --port 8000

# ── Build ────────────────────────────────────────────────────
build:
	python build.py
