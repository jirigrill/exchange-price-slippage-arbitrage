# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Using Makefile (Recommended)
- **Show all available commands**: `make help`
- **Quick development setup**: `make dev` (install + format + test + run)
- **Auto-fix code issues**: `make fix` (remove unused imports + sort imports + format)
- **Pre-commit checks**: `make check` (fix + lint + unit tests)
- **Full CI pipeline**: `make ci` (install + fix + lint + all tests)

### Development
- **Install dependencies**: `make install` or `uv sync`
- **Run the application**: `make run` or `uv run python main.py`
- **Format code**: `make format` or `uv run black .`
- **Auto-fix code issues**: `make fix` or run autoflake + isort + black
- **Lint code**: `make lint` or `uv run flake8 .`
- **Clean cache files**: `make clean`

### Testing
- **Run all tests**: `make test` or `uv run pytest`
- **Run unit tests only**: `make test-unit` or `uv run python tests/test_runner.py unit`
- **Run integration tests**: `make test-integration` or `uv run python tests/test_runner.py integration`
- **Run with coverage**: `make test-coverage` or `uv run python tests/test_runner.py coverage`
- **Test Telegram integration**: `make telegram-test` or `uv run python tests/integration/test_telegram.py`
- **Run specific test file**: `uv run pytest tests/unit/test_coinmate_api.py`

### Docker Deployment
- **Build Docker image**: `make docker-build`
- **Run with Docker Compose**: `make docker-run` or `docker-compose up -d`
- **Deploy with production settings**: `make docker-deploy` or `./deploy.sh`

## Architecture Overview

This is a Bitcoin arbitrage monitoring system that detects price differences between exchanges and sends alerts when profitable opportunities arise.

### Core Components

**Entry Point**: `main.py` - Orchestrates the monitoring loop, initializes all services, and handles the main application flow.

**Exchange Integration** (`src/apis/`):
- `kraken_api.py` - Handles BTC/USD price fetching from Kraken
- `coinmate_api.py` - Handles BTC/CZK price fetching from Coinmate

**Business Logic** (`src/core/`):
- `exchange_monitor.py` - Manages real-time price monitoring across exchanges, handles currency conversion
- `arbitrage_detector.py` - Calculates arbitrage opportunities, applies configurable trading fees, filters by profit thresholds

**Services** (`src/services/`):
- `currency_converter.py` - Converts CZK to USD using live exchange rates
- `telegram_service.py` - Sends alerts when profitable opportunities are detected

**Configuration** (`config/settings.py`):
- Exchange definitions: `LARGE_EXCHANGES` (Kraken), `SMALL_EXCHANGES` (Coinmate)
- Trading pairs: `EXCHANGE_TRADING_PAIRS` maps exchanges to their specific pairs
- Profit thresholds: `MIN_PROFIT_PERCENTAGE` (used for both detection and Telegram alerts)
- Trading fees: Configurable per exchange (`KRAKEN_TRADING_FEE`, `COINMATE_TRADING_FEE`) with dynamic fetching option
- Telegram control: `TELEGRAM_ENABLED` allows completely disabling notifications

### Data Flow

1. `ExchangeMonitor` fetches prices from both exchanges simultaneously
2. `CurrencyConverter` converts CZK prices to USD for comparison
3. `ArbitrageDetector` calculates profit opportunities between exchange pairs (including fee calculations)
4. `TelegramService` sends alerts for opportunities above the threshold (if enabled)
5. Main loop logs all activity including detailed fee calculations and continues monitoring

### Key Architecture Decisions

- **Async/await**: All API calls are asynchronous for concurrent price fetching
- **Multi-currency support**: Prices are normalized to USD for accurate comparison
- **Modular exchange integration**: New exchanges can be added by implementing API clients in `src/apis/`
- **Profit-based filtering**: Only opportunities above configurable thresholds are reported

### Environment Configuration

The system requires minimal configuration and works without API keys for basic monitoring:
- `.env` file contains optional API keys, trading fees, and Telegram credentials
- All settings have sensible defaults in `config/settings.py`
- Trading fees are configurable per exchange with optional dynamic fetching
- Telegram notifications can be completely disabled via `TELEGRAM_ENABLED=false`
- When enabled, Telegram requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (alerts sent for all detected opportunities)

### Testing Strategy

- **Unit tests** (`tests/unit/`) - Mock external APIs, test individual components
- **Integration tests** (`tests/integration/`) - Test real API interactions
- **Test markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- **68 total tests** covering all major components and error scenarios