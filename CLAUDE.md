# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development
- **Run the application**: `uv run python main.py`
- **Install dependencies**: `uv sync`
- **Format code**: `uv run black .`
- **Lint code**: `uv run flake8 .`

### Testing
- **Run all tests**: `uv run pytest`
- **Run unit tests only**: `uv run python tests/test_runner.py unit`
- **Run integration tests**: `uv run python tests/test_runner.py integration`
- **Run with coverage**: `uv run python tests/test_runner.py coverage`
- **Run specific test file**: `uv run pytest tests/unit/test_coinmate_api.py`
- **Test Telegram integration**: `uv run python tests/integration/test_telegram.py`

### Docker Deployment
- **Deploy with Docker**: `./deploy.sh`
- **Run with Docker Compose**: `docker-compose up -d`

## Architecture Overview

This is a Bitcoin arbitrage monitoring system that detects price differences between exchanges and sends alerts when profitable opportunities arise.

### Core Components

**Entry Point**: `main.py` - Orchestrates the monitoring loop, initializes all services, and handles the main application flow.

**Exchange Integration** (`src/apis/`):
- `kraken_api.py` - Handles BTC/USD price fetching from Kraken
- `coinmate_api.py` - Handles BTC/CZK price fetching from Coinmate

**Business Logic** (`src/core/`):
- `exchange_monitor.py` - Manages real-time price monitoring across exchanges, handles currency conversion
- `arbitrage_detector.py` - Calculates arbitrage opportunities, applies trading fees, filters by profit thresholds

**Services** (`src/services/`):
- `currency_converter.py` - Converts CZK to USD using live exchange rates
- `telegram_service.py` - Sends alerts when profitable opportunities are detected

**Configuration** (`config/settings.py`):
- Exchange definitions: `LARGE_EXCHANGES` (Kraken), `SMALL_EXCHANGES` (Coinmate)
- Trading pairs: `EXCHANGE_TRADING_PAIRS` maps exchanges to their specific pairs
- Profit thresholds: `MIN_PROFIT_PERCENTAGE`, `TELEGRAM_ALERT_THRESHOLD`

### Data Flow

1. `ExchangeMonitor` fetches prices from both exchanges simultaneously
2. `CurrencyConverter` converts CZK prices to USD for comparison
3. `ArbitrageDetector` calculates profit opportunities between exchange pairs
4. `TelegramService` sends alerts for opportunities above the threshold
5. Main loop logs all activity and continues monitoring

### Key Architecture Decisions

- **Async/await**: All API calls are asynchronous for concurrent price fetching
- **Multi-currency support**: Prices are normalized to USD for accurate comparison
- **Modular exchange integration**: New exchanges can be added by implementing API clients in `src/apis/`
- **Profit-based filtering**: Only opportunities above configurable thresholds are reported

### Environment Configuration

The system requires minimal configuration and works without API keys for basic monitoring:
- `.env` file contains optional API keys and Telegram credentials
- All settings have sensible defaults in `config/settings.py`
- Telegram notifications require `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

### Testing Strategy

- **Unit tests** (`tests/unit/`) - Mock external APIs, test individual components
- **Integration tests** (`tests/integration/`) - Test real API interactions
- **Test markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- **68 total tests** covering all major components and error scenarios