.PHONY: help install run test test-unit test-integration test-coverage format lint fix clean docker-build docker-run docker-deploy telegram-test db-up db-down db-logs db-reset db-test db-ensure db-connect db-timezone grafana-up grafana-down grafana-logs jupyter-up jupyter-down jupyter-logs jupyter-restart

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
	@echo "Database (Optional):"
	@echo "  db-up            Start TimescaleDB container"
	@echo "  db-down          Stop TimescaleDB container"
	@echo "  db-logs          View database logs"
	@echo "  db-reset         Reset database (destructive!)"
	@echo "  db-test          Run database integration tests"
	@echo "  db-connect       Connect to database with local timezone"
	@echo "  db-timezone      Set database default timezone from .env"
	@echo "  Note: 'make run' auto-starts database if enabled"
	@echo ""
	@echo "Analytics (Optional):"
	@echo "  grafana-up       Start Grafana dashboard for data analysis"
	@echo "  grafana-down     Stop Grafana"
	@echo "  grafana-logs     View Grafana logs"
	@echo "  jupyter-up       Start Jupyter notebook server for hypothesis testing"
	@echo "  jupyter-down     Stop Jupyter server"
	@echo "  jupyter-logs     View Jupyter logs"
	@echo "  jupyter-restart  Restart Jupyter server"
	@echo ""
	@echo "Example: make install && make test-unit && make run"

# Development commands
install:
	uv sync

run: db-ensure
	uv run python main.py

# Check if database is needed and start if required
db-ensure:
	@DB_ENABLED=$$(uv run python -c "from config.settings import DATABASE_ENABLED; print('true' if DATABASE_ENABLED else 'false')") && \
	DB_RUNNING=$$(docker ps -q --filter 'name=timescaledb' | wc -l | tr -d ' ') && \
	if [ "$$DB_ENABLED" = "true" ] && [ "$$DB_RUNNING" = "0" ]; then \
		echo "🔄 Database required but not running - starting TimescaleDB..."; \
		make db-up; \
	elif [ "$$DB_ENABLED" = "false" ]; then \
		echo "📊 Database disabled - running without TimescaleDB"; \
	elif [ "$$DB_ENABLED" = "true" ] && [ "$$DB_RUNNING" != "0" ]; then \
		echo "✅ TimescaleDB already running"; \
	fi

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
	cd deployment/docker && docker build -t bitcoin-arbitrage .

docker-run:
	cd deployment/docker && docker-compose up -d

docker-deploy:
	./deployment/scripts/deploy.sh

# Quality checks (run before committing)
check: fix lint test-unit
	@echo "✅ All quality checks passed!"

# Quick development cycle
dev: install format test-unit db-ensure run

# Full CI pipeline
ci: install fix lint test
	@echo "✅ CI pipeline completed successfully!"

# Database commands
db-up:
	cd deployment/docker && docker-compose up -d timescaledb
	@echo "⏳ Waiting for database to be ready..."
	@sleep 10
	@DATABASE_PORT=$$(uv run python -c "from config.settings import DATABASE_PORT; print(DATABASE_PORT)") && \
	echo "✅ TimescaleDB is running on port $$DATABASE_PORT"

db-down:
	cd deployment/docker && docker-compose down timescaledb

db-logs:
	cd deployment/docker && docker-compose logs -f timescaledb

db-reset:
	@echo "⚠️  This will delete all database data! Press Ctrl+C to cancel..."
	@sleep 5
	cd deployment/docker && docker-compose down timescaledb
	docker volume rm exchange-price-slippage-arbitrage_timescale_data 2>/dev/null || true
	cd deployment/docker && docker-compose up -d timescaledb
	@echo "🔄 Database reset complete"

db-test: db-up
	@echo "🧪 Running database integration tests..."
	SKIP_DB_INTEGRATION=false uv run pytest tests/integration/test_database_integration.py -v

db-connect:
	@TIMEZONE=$$(uv run python -c "from config.settings import TIMEZONE; print(TIMEZONE)") && \
	DATABASE_USER=$$(uv run python -c "from config.settings import DATABASE_USER; print(DATABASE_USER)") && \
	DATABASE_NAME=$$(uv run python -c "from config.settings import DATABASE_NAME; print(DATABASE_NAME)") && \
	echo "🔗 Connecting to database with timezone: $$TIMEZONE" && \
	docker exec -it $(shell docker ps -q --filter "name=timescaledb") psql -U $$DATABASE_USER -d $$DATABASE_NAME -c "SET timezone = '$$TIMEZONE';" -c "\echo 'Timezone set to $$TIMEZONE. Use exchange_prices_local view for local time display.'" && \
	docker exec -it $(shell docker ps -q --filter "name=timescaledb") psql -U $$DATABASE_USER -d $$DATABASE_NAME

db-timezone:
	@TIMEZONE=$$(uv run python -c "from config.settings import TIMEZONE; print(TIMEZONE)") && \
	DATABASE_USER=$$(uv run python -c "from config.settings import DATABASE_USER; print(DATABASE_USER)") && \
	DATABASE_NAME=$$(uv run python -c "from config.settings import DATABASE_NAME; print(DATABASE_NAME)") && \
	echo "🕒 Setting database default timezone to: $$TIMEZONE" && \
	docker exec $(shell docker ps -q --filter "name=timescaledb") psql -U $$DATABASE_USER -d $$DATABASE_NAME -c "ALTER DATABASE $$DATABASE_NAME SET timezone = '$$TIMEZONE';" && \
	echo "✅ Database default timezone updated. Restart database for full effect."

# Grafana commands
grafana-up: db-ensure
	@GRAFANA_ENABLED=$$(uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GRAFANA_ENABLED', 'true').lower())") && \
	if [ "$$GRAFANA_ENABLED" = "true" ]; then \
		echo "📊 Starting Grafana dashboard..."; \
		cd deployment/docker && docker-compose -f docker-compose.yml -f docker-compose.grafana.yml up -d grafana; \
		GRAFANA_PORT=$$(uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GRAFANA_PORT', '3000'))") && \
		echo "✅ Grafana available at http://localhost:$$GRAFANA_PORT"; \
		echo "💡 Default login: admin / (check GRAFANA_ADMIN_PASSWORD in .env)"; \
	else \
		echo "📊 Grafana disabled via GRAFANA_ENABLED=false"; \
	fi

grafana-down:
	cd deployment/docker && docker-compose -f docker-compose.yml -f docker-compose.grafana.yml down grafana

grafana-logs:
	cd deployment/docker && docker-compose -f docker-compose.yml -f docker-compose.grafana.yml logs -f grafana

# Jupyter notebook commands
jupyter-up:
	@echo "🚀 Starting Jupyter notebook server..."
	cd deployment/docker && docker-compose -f docker-compose.jupyter.yml up -d
	@echo "📊 Jupyter server starting..."
	@sleep 5
	@echo "🔗 Jupyter will be available at: http://localhost:8888"
	@echo "🔑 Access token: $(shell grep JUPYTER_TOKEN .env | cut -d'=' -f2)"
	@echo "📁 Notebooks directory: ./analytics/notebooks"
	@echo "📈 Database connection configured automatically"

jupyter-down:
	cd deployment/docker && docker-compose -f docker-compose.jupyter.yml down

jupyter-logs:
	cd deployment/docker && docker-compose -f docker-compose.jupyter.yml logs -f jupyter

jupyter-restart:
	make jupyter-down
	make jupyter-up