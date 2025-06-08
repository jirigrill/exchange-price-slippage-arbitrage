.PHONY: help install run test test-unit test-integration test-coverage format lint fix clean docker-build docker-run docker-deploy telegram-test

# Default target
help:
	@echo "Bitcoin Arbitrage Monitor - Available Commands"
	@echo "=============================================="
	@echo ""
	@echo "Development:"
	@echo "  install          Install dependencies with uv"
	@echo "  run              Run the arbitrage monitor"
	@echo "  format           Format code with black"
	@echo "  lint             Lint code with flake8"
	@echo "  fix              Auto-fix lint issues (imports, format)"
	@echo "  clean            Clean cache and temp files"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  telegram-test    Test Telegram integration"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run with Docker Compose"
	@echo "  docker-deploy    Deploy with production settings"
	@echo ""
	@echo "Example: make install && make test-unit && make run"

# Development commands
install:
	uv sync

run:
	uv run python main.py

format:
	uv run black .

lint:
	uv run flake8 .

fix:
	uv run autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive .
	uv run isort .
	uv run black .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

# Testing commands
test:
	uv run pytest

test-unit:
	uv run python tests/test_runner.py unit

test-integration:
	uv run python tests/test_runner.py integration

test-coverage:
	uv run python tests/test_runner.py coverage

telegram-test:
	uv run python tests/integration/test_telegram.py

# Docker commands
docker-build:
	docker build -t bitcoin-arbitrage .

docker-run:
	docker-compose up -d

docker-deploy:
	./deploy.sh

# Quality checks (run before committing)
check: fix lint test-unit
	@echo "✅ All quality checks passed!"

# Quick development cycle
dev: install format test-unit run

# Full CI pipeline
ci: install fix lint test
	@echo "✅ CI pipeline completed successfully!"