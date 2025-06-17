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
- **Start Grafana monitoring**: `docker-compose -f docker-compose.grafana.yml up -d`
- **Start Jupyter notebooks**: `docker-compose -f docker-compose.jupyter.yml up -d`

### Database Operations (Optional)
- **Auto-start database**: `make run` (automatically starts TimescaleDB if enabled and not running)
- **Start TimescaleDB manually**: `make db-up` (starts database container)
- **Stop TimescaleDB**: `make db-down`
- **View database logs**: `make db-logs`
- **Reset database**: `make db-reset` (⚠️ destructive - deletes all data)
- **Test database integration**: `make db-test` (runs with real database)
- **Connect with timezone**: `make db-connect` (connects with your local timezone automatically)
- **Set default timezone**: `make db-timezone` (sets database timezone from TIMEZONE environment variable)
- **Run without database**: `DATABASE_ENABLED=false make run` (disables all database operations)

### Monitoring & Analytics (Optional)
- **Start Grafana dashboards**: `docker-compose -f docker-compose.grafana.yml up -d` (access at http://localhost:3000)
- **Start Jupyter notebooks**: `docker-compose -f docker-compose.jupyter.yml up -d` (access at http://localhost:8888)
- **View Grafana dashboards**: `open http://localhost:3000` (admin/admin)
- **Access Jupyter notebooks**: `open http://localhost:8888`
- **Grafana datasource config**: Edit `grafana/datasources/timescaledb.yml`
- **Grafana dashboard config**: Edit `grafana/dashboards/bitcoin-arbitrage.json`
- **Jupyter dependencies**: `jupyter-requirements.txt` contains notebook-specific packages

## Architecture Overview

This is a Bitcoin arbitrage monitoring system that detects price differences between exchanges and sends alerts when profitable opportunities arise.

### Core Components

**Entry Point**: `main.py` - Orchestrates the monitoring loop, initializes all services, and handles the main application flow.

**Exchange Integration** (`src/apis/`):
- `base_exchange.py` - Abstract base class defining the exchange API interface
- `kraken_api.py` - Handles BTC/USD price fetching from Kraken (inherits from BaseExchangeAPI)
- `coinmate_api.py` - Handles BTC/CZK price fetching from Coinmate (inherits from BaseExchangeAPI)

**Business Logic** (`src/core/`):
- `exchange_monitor.py` - Manages real-time price monitoring across exchanges, handles currency conversion
- `arbitrage_detector.py` - Calculates arbitrage opportunities, applies configurable trading fees, filters by profit thresholds

**Services** (`src/services/`):
- `currency_converter.py` - Converts CZK to USD using live exchange rates
- `telegram_service.py` - Sends alerts when profitable opportunities are detected
- `database_service.py` - Stores price data and arbitrage opportunities in TimescaleDB

**Monitoring & Analytics** (Optional):
- `grafana/` - Grafana dashboards and datasource configurations for real-time monitoring
- `notebooks/` - Jupyter notebooks for historical data analysis and backtesting
- `coinmate_signature.py` - Utility for Coinmate API signature generation

**Configuration** (`config/settings.py`):
- Exchange definitions: `LARGE_EXCHANGES` (Kraken), `SMALL_EXCHANGES` (Coinmate)
- Trading pairs: `EXCHANGE_TRADING_PAIRS` maps exchanges to their specific pairs
- Profit thresholds: `MIN_PROFIT_PERCENTAGE` (used for both detection and Telegram alerts)
- Trading fees: Configurable per exchange (`KRAKEN_TRADING_FEE`, `COINMATE_TRADING_FEE`) with dynamic fetching option
- Telegram control: `TELEGRAM_ENABLED` allows completely disabling notifications
- Database control: `DATABASE_ENABLED` allows disabling TimescaleDB storage

### Data Flow

1. `ExchangeMonitor` fetches prices from both exchanges simultaneously
2. `CurrencyConverter` converts CZK prices to USD for comparison
3. `DatabaseService` stores price data and exchange health status (if enabled)
4. `ArbitrageDetector` calculates profit opportunities between exchange pairs (including fee calculations)
5. `DatabaseService` stores detected arbitrage opportunities (if enabled)
6. `TelegramService` sends alerts for opportunities above the threshold (if enabled)
7. Main loop logs all activity including detailed fee calculations and continues monitoring

### Key Architecture Decisions

- **Async/await**: All API calls are asynchronous for concurrent price fetching
- **Multi-currency support**: Prices are normalized to USD for accurate comparison
- **Abstract base class pattern**: All exchange APIs inherit from BaseExchangeAPI for consistency and polymorphism
- **Factory pattern**: Exchange APIs are created via factory function for flexible instantiation
- **Modular exchange integration**: New exchanges can be added by inheriting from BaseExchangeAPI
- **Profit-based filtering**: Only opportunities above configurable thresholds are reported
- **TimescaleDB integration**: Historical price and arbitrage data stored in time-series database
- **Non-blocking storage**: Database operations don't impact real-time monitoring performance
- **Visual monitoring**: Optional Grafana dashboards for real-time data visualization
- **Data analysis**: Jupyter notebooks for advanced analytics and backtesting
- **Containerized deployment**: Multiple Docker Compose configurations for different use cases

### Environment Configuration

The system requires minimal configuration and works without API keys for basic monitoring:
- `.env` file contains optional API keys, trading fees, and Telegram credentials
- All settings have sensible defaults in `config/settings.py`
- Trading fees are configurable per exchange with optional dynamic fetching
- Telegram notifications can be completely disabled via `TELEGRAM_ENABLED=false`
- When enabled, Telegram requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (alerts sent for all detected opportunities)

### Database Configuration (Optional)

- **Database storage is completely optional** - the system works perfectly without it
- Database can be disabled via `DATABASE_ENABLED=false` in `.env` or environment variable
- When enabled (default), stores historical price data and arbitrage opportunities in TimescaleDB
- `make run` automatically starts TimescaleDB container if database is enabled and container not running
- Graceful fallback: if database connection fails, system continues without database storage
- When enabled, requires TimescaleDB connection via configurable settings (defaults to localhost:5433)
- **Timezone Support**: Set `TIMEZONE` environment variable (e.g., `Europe/Berlin`, `America/New_York`, `UTC`) for automatic timestamp conversion in database queries

### Testing Strategy

- **Unit tests** (`tests/unit/`) - Mock external APIs, test individual components including:
  - `test_base_exchange.py` - Tests for abstract base class interface
  - `test_database_service.py` - Database service tests
  - `test_coinmate_api.py`, `test_kraken_api.py` - Exchange API tests
  - `test_arbitrage_detector.py`, `test_currency_converter.py` - Core logic tests
  - `test_telegram_service.py` - Notification service tests
- **Integration tests** (`tests/integration/`) - Test real API interactions
  - `test_database_integration.py` - Database integration tests
  - `test_telegram.py` - Telegram API integration tests
- **Database integration tests** - Test TimescaleDB operations with real database (via `make db-test`)
- **Test markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- **100+ total tests** covering all major components and error scenarios
- **Abstract base class testing**: Tests for BaseExchangeAPI interface and polymorphism

## TimescaleDB Database Schema & Analytics

The system uses TimescaleDB (PostgreSQL extension) for time-series data storage and analytics. Database is completely optional - the system works perfectly without it.

### Database Tables

#### 1. `exchange_prices` - Price data from all exchanges
```sql
CREATE TABLE exchange_prices (
    id SERIAL,
    exchange_name VARCHAR(50) NOT NULL,    -- 'kraken', 'coinmate'
    symbol VARCHAR(20) NOT NULL,           -- 'BTC/USD', 'BTC/CZK'
    price DECIMAL(15,8) NOT NULL,          -- Price in original currency
    price_usd DECIMAL(15,8) NOT NULL,      -- Price converted to USD
    original_currency VARCHAR(10) NOT NULL, -- 'USD', 'CZK'
    volume DECIMAL(20,8) DEFAULT 0,        -- Trading volume
    timestamp TIMESTAMPTZ NOT NULL,        -- When price was fetched
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 2. `arbitrage_opportunities` - Detected profit opportunities
```sql
CREATE TABLE arbitrage_opportunities (
    id SERIAL,
    buy_exchange VARCHAR(50) NOT NULL,     -- Exchange to buy from
    sell_exchange VARCHAR(50) NOT NULL,    -- Exchange to sell on
    buy_price DECIMAL(15,8) NOT NULL,      -- Buy price (USD)
    sell_price DECIMAL(15,8) NOT NULL,     -- Sell price (USD)
    profit_usd DECIMAL(15,8) NOT NULL,     -- Profit in USD
    profit_percentage DECIMAL(8,4) NOT NULL, -- Net profit percentage (after fees)
    volume_limit DECIMAL(20,8) NOT NULL,   -- Max tradeable volume
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3. `exchange_status` - Exchange health monitoring
```sql
CREATE TABLE exchange_status (
    id SERIAL,
    exchange_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,           -- 'active', 'error', 'timeout'
    error_message TEXT,                    -- Error details if status != 'active'
    response_time_ms INTEGER,              -- API response time
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

### SQL Query Examples

**Note**: The DatabaseService automatically handles timezone conversion based on your `TIMEZONE` environment variable. When using the programmatic methods like `get_latest_prices()`, `get_arbitrage_opportunities()`, etc., timestamps are automatically converted to your configured timezone. For direct SQL queries, you can manually add `AT TIME ZONE 'YourTimezone'` or use the convenience views below.

#### Latest Prices
```sql
-- Get current prices from all exchanges
SELECT * FROM get_latest_prices();

-- Get latest BTC prices with spread calculation and local time
-- Note: Replace 'Your/Timezone' with your timezone from TIMEZONE environment variable
SELECT 
    exchange_name,
    price_usd,
    price_usd - (SELECT MIN(price_usd) FROM latest_exchange_prices WHERE symbol LIKE '%BTC%') as spread_from_lowest,
    timestamp AT TIME ZONE 'Your/Timezone' as local_time
FROM latest_exchange_prices 
WHERE symbol LIKE '%BTC%'
ORDER BY price_usd;

-- Check recent price updates (last 5 minutes)
SELECT 
    exchange_name,
    price_usd,
    timestamp AT TIME ZONE 'Your/Timezone' as local_time,
    NOW() - timestamp as age
FROM latest_exchange_prices 
WHERE timestamp >= NOW() - INTERVAL '5 minutes'
ORDER BY timestamp DESC;
```

#### Arbitrage Opportunities
```sql
-- Get recent arbitrage opportunities (last 24 hours) with local time
-- Note: Replace 'Your/Timezone' with your timezone from TIMEZONE environment variable
SELECT 
    buy_exchange,
    sell_exchange,
    buy_price,
    sell_price,
    profit_percentage,
    profit_usd,
    timestamp AT TIME ZONE 'Your/Timezone' as local_time
FROM arbitrage_opportunities 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY profit_percentage DESC 
LIMIT 20;

-- Best opportunities by exchange pair
SELECT 
    buy_exchange || ' → ' || sell_exchange as trade_direction,
    COUNT(*) as opportunity_count,
    AVG(profit_percentage) as avg_profit_pct,
    MAX(profit_percentage) as max_profit_pct,
    SUM(profit_usd) as total_profit_potential
FROM arbitrage_opportunities 
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY buy_exchange, sell_exchange
ORDER BY max_profit_pct DESC;
```

#### Price History & Analytics
```sql
-- Hourly price spread analysis (last 24 hours)
SELECT * FROM get_price_spread_history(24);

-- Price volatility by exchange
SELECT 
    exchange_name,
    DATE_TRUNC('hour', timestamp) as hour,
    MIN(price_usd) as low,
    MAX(price_usd) as high,
    (MAX(price_usd) - MIN(price_usd)) as volatility_usd,
    ((MAX(price_usd) - MIN(price_usd)) / MIN(price_usd)) * 100 as volatility_pct
FROM exchange_prices 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
    AND symbol LIKE '%BTC%'
GROUP BY exchange_name, hour
ORDER BY hour DESC, volatility_pct DESC;

-- Daily arbitrage summary using continuous aggregates
SELECT 
    bucket::DATE as date,
    buy_exchange,
    sell_exchange,
    opportunity_count,
    avg_profit_percentage,
    max_profit_percentage,
    total_profit_usd
FROM arbitrage_daily 
WHERE bucket >= NOW() - INTERVAL '30 days'
ORDER BY bucket DESC, max_profit_percentage DESC;
```

#### Exchange Health Monitoring
```sql
-- Exchange uptime and performance (last 24 hours)
SELECT 
    exchange_name,
    COUNT(*) as total_requests,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as successful_requests,
    ROUND(
        (COUNT(CASE WHEN status = 'active' THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2
    ) as success_rate_pct,
    AVG(response_time_ms) as avg_response_time_ms,
    MAX(timestamp) as last_seen
FROM exchange_status 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY exchange_name
ORDER BY success_rate_pct DESC;

-- Recent errors by exchange
SELECT 
    exchange_name,
    error_message,
    COUNT(*) as error_count,
    MAX(timestamp) as last_occurrence
FROM exchange_status 
WHERE status != 'active'
    AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY exchange_name, error_message
ORDER BY last_occurrence DESC;
```

#### Database Maintenance
```sql
-- Check table sizes and row counts
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_tup_ins as inserts,
    n_tup_del as deletes
FROM pg_stat_user_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- View TimescaleDB chunk information
SELECT 
    chunk_schema,
    chunk_name,
    range_start,
    range_end,
    pg_size_pretty(pg_total_relation_size(format('%I.%I', chunk_schema, chunk_name))) as chunk_size
FROM timescaledb_information.chunks
WHERE hypertable_name = 'exchange_prices'
ORDER BY range_start DESC;

-- Clean up old data (manual cleanup)
DELETE FROM exchange_prices WHERE timestamp < NOW() - INTERVAL '30 days';
DELETE FROM arbitrage_opportunities WHERE timestamp < NOW() - INTERVAL '30 days';
DELETE FROM exchange_status WHERE timestamp < NOW() - INTERVAL '7 days';
```

### Database Performance Features

- **Hypertables**: Automatic partitioning by time for optimal query performance
- **Continuous Aggregates**: Pre-computed hourly and daily summaries for fast analytics
- **Materialized Views**: `price_1h` and `arbitrage_daily` for quick historical analysis
- **Optimized Indexes**: On exchange+timestamp, symbol+timestamp, and profit percentage
- **Built-in Functions**: `get_latest_prices()` and `get_price_spread_history(hours)`
- **Data Retention**: Configurable automatic cleanup of old data (disabled by default)

### Connecting to Database

```bash
# Method 1: Using make command with automatic timezone (recommended)
make db-connect  # Connects with your TIMEZONE setting automatically

# Method 2: Set database default timezone (one-time setup)
make db-timezone  # Sets database default to your TIMEZONE from .env

# Method 3: Using Docker directly (shows UTC timestamps by default)
docker exec -it $(docker ps -q --filter "name=timescaledb") psql -U arbitrage_user -d arbitrage

# Method 4: Using psql directly (if PostgreSQL client installed)
psql postgresql://arbitrage_user:arbitrage_pass@localhost:5433/arbitrage
```

### Timezone Behavior

- **Data Storage**: All timestamps stored in UTC (database default)
- **Raw Queries**: `SELECT * FROM exchange_prices` shows UTC timestamps  
- **Timezone Conversion**: Use `make db-connect` or `SET timezone = 'YourTimezone';` 
- **Programmatic Access**: DatabaseService methods automatically convert to your `TIMEZONE` setting

```sql
-- Raw table always shows stored timezone (UTC)
SELECT timestamp FROM exchange_prices LIMIT 1;
-- Result: 2025-06-11 19:03:58.923225+00

-- Use convenience views for local time (recommended approach):
SELECT local_timestamp, utc_timestamp FROM exchange_prices_local LIMIT 1;
-- Result: local_timestamp: 2025-06-11 21:03:58.923225, utc_timestamp: 2025-06-11 19:03:58.923225+00

-- Alternative: Manual timezone conversion (example for UTC+2)
SELECT timestamp + INTERVAL '2 hours' as local_time FROM exchange_prices LIMIT 1;
-- Result: 2025-06-11 21:03:58.923225

-- Set database session timezone (optional)
SET timezone = 'Your/Timezone';
SELECT NOW() as current_local_time;
-- Result: timestamp in your configured timezone
```

### Convenience Views

The system provides timezone-aware views that automatically convert UTC to local time:

```sql
-- View exchange prices with local time conversion
SELECT * FROM exchange_prices_local ORDER BY local_timestamp DESC LIMIT 5;
-- Shows local_timestamp (your timezone) and utc_timestamp (original UTC)

-- View arbitrage opportunities with local time conversion
SELECT * FROM arbitrage_opportunities_local ORDER BY local_timestamp DESC LIMIT 5;
-- Shows local_timestamp (your timezone) and utc_timestamp (original UTC)

-- Compare UTC vs local time
SELECT 
    exchange_name,
    utc_timestamp as stored_utc,
    local_timestamp as your_local_time,
    'Timezone offset applied' as note
FROM exchange_prices_local 
ORDER BY utc_timestamp DESC LIMIT 3;
```

### Database Commands

```bash
# Connect to database with timezone setting
make db-connect

# Set database default timezone from .env file
make db-timezone

# Manual timezone setting (in psql session)
SET timezone = 'Your/Timezone';
```

## Monitoring & Analytics Features

This section covers the optional monitoring and analytics components that enhance the core arbitrage monitoring system.

### Grafana Dashboards

**Location**: `grafana/` directory
**Purpose**: Real-time visualization of arbitrage opportunities and system metrics

#### Key Files:
- `grafana/dashboards/bitcoin-arbitrage.json` - Main Bitcoin arbitrage monitoring dashboard
- `grafana/dashboards/dashboard.yml` - Dashboard provisioning configuration
- `grafana/datasources/timescaledb.yml` - TimescaleDB datasource configuration

#### Dashboard Features:
- Real-time price differences between exchanges
- Historical arbitrage opportunity tracking
- Exchange API response times and health monitoring
- Profit potential analysis and trends
- Alert threshold visualization

#### Usage:
```bash
# Start Grafana with TimescaleDB
docker-compose -f docker-compose.grafana.yml up -d

# Access dashboard at http://localhost:3000
# Default credentials: admin/admin
```

### Jupyter Notebooks

**Location**: `notebooks/` directory
**Purpose**: Advanced data analysis, backtesting, and research

#### Key Files:
- `notebooks/arbitrage_analysis.ipynb` - Comprehensive market analysis notebook
- `jupyter-requirements.txt` - Jupyter-specific dependencies (numpy, pandas, matplotlib, etc.)

#### Analysis Capabilities:
- Historical arbitrage opportunity analysis
- Price spread trends and statistical analysis
- Exchange performance comparison
- Profit potential modeling and backtesting
- Market volatility analysis
- Custom data visualization

#### Usage:
```bash
# Start Jupyter notebook server
docker-compose -f docker-compose.jupyter.yml up -d

# Access notebooks at http://localhost:8888
# No password required (development setup)
```

### Additional Utilities

#### Coinmate Signature Utility
**File**: `coinmate_signature.py`
**Purpose**: Handles Coinmate API authentication signature generation
**Note**: This is a standalone utility file that supports the Coinmate API integration

### Docker Compose Configurations

The project includes multiple Docker Compose files for different deployment scenarios:

1. **`docker-compose.yml`** - Basic application + TimescaleDB
2. **`docker-compose.grafana.yml`** - Full monitoring stack (app + database + Grafana)
3. **`docker-compose.jupyter.yml`** - Analytics setup (app + database + Jupyter)

#### Example Usage Scenarios:

```bash
# Scenario 1: Basic monitoring only
docker-compose up -d

# Scenario 2: Full monitoring with Grafana dashboards
docker-compose -f docker-compose.grafana.yml up -d

# Scenario 3: Research and analysis with Jupyter
docker-compose -f docker-compose.jupyter.yml up -d

# Scenario 4: Everything (run multiple compose files)
docker-compose up -d
docker-compose -f docker-compose.grafana.yml up grafana -d
docker-compose -f docker-compose.jupyter.yml up jupyter -d
```

### Integration with Core System

Both monitoring features integrate seamlessly with the core arbitrage monitoring system:

- **Data Source**: Both Grafana and Jupyter use the same TimescaleDB database
- **Real-time Updates**: Grafana dashboards update automatically as new data arrives
- **Historical Analysis**: Jupyter notebooks can analyze any time period stored in the database
- **Optional Components**: Both can be disabled without affecting core functionality
- **Independent Operation**: Can run separately or together based on needs

### Development and Customization

#### Grafana Customization:
- Edit dashboard JSON files in `grafana/dashboards/`
- Modify datasource settings in `grafana/datasources/`
- Add new dashboards by creating additional JSON files

#### Jupyter Customization:
- Add new analysis notebooks to `notebooks/` directory
- Install additional Python packages in `jupyter-requirements.txt`
- Create custom analysis scripts and visualizations

### Performance Considerations

- **Grafana**: Minimal impact on system performance, queries database efficiently
- **Jupyter**: Resource usage depends on analysis complexity, runs independently
- **Database**: Both tools use read-only queries, no impact on data collection
- **Docker Resources**: Each service can be resource-limited via Docker Compose configuration