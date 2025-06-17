# Bitcoin Arbitrage Monitor

A Python-based system for monitoring Bitcoin price arbitrage opportunities between international and Czech cryptocurrency exchanges.

## Overview

This project monitors Bitcoin prices in real-time and identifies profitable arbitrage opportunities by comparing prices from:
- **International exchanges** (Kraken - BTC/USD)  
- **Czech exchanges** (Coinmate - BTC/CZK)

The system automatically converts all prices to USD for accurate comparison and profit calculation.

### How It Works

1. **Multi-Currency Monitoring**: Fetches BTC prices in USD and CZK from different exchanges
2. **Currency Conversion**: Converts all prices to USD using real-time exchange rates
3. **Arbitrage Detection**: Identifies profitable price differences between exchanges
4. **Profit Calculation**: Calculates net profit after trading fees and currency conversion
5. **Real-Time Updates**: Continuously monitors for new opportunities

## Features

- ✅ **Multi-Exchange Support**: Kraken (international) + Coinmate (Czech)
- ✅ **Multi-Currency Handling**: BTC/USD and BTC/CZK with automatic USD conversion
- ✅ **Real-Time Exchange Rates**: Live currency conversion via external API
- ✅ **Native APIs**: Direct Kraken and Coinmate API integration (no third-party libraries)
- ✅ **Arbitrage Detection**: Automated opportunity identification with profit calculations
- ✅ **Configurable Trading Fees**: Per-exchange fee configuration with optional dynamic fetching
- ✅ **Telegram Notifications**: Instant alerts for profitable opportunities (can be disabled)
- ✅ **TimescaleDB Integration**: Optional historical data storage and analytics (fully optional)
- ✅ **Abstract Exchange API**: Polymorphic interface for easy exchange expansion
- ✅ **Async Architecture**: Efficient concurrent price monitoring
- ✅ **Auto Database Management**: Smart container startup and graceful fallback
- ✅ **Comprehensive Testing**: Full pytest suite with 100+ tests
- ✅ **Environment Configuration**: Flexible setup via environment variables

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

### Prerequisites

- Python 3.9+
- uv package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd exchange-price-slippage-arbitrage
   ```

2. **Install dependencies**
   ```bash
   # Using Makefile (recommended)
   make install
   
   # Or directly with uv
   uv sync
   ```

3. **Configure environment variables (optional)**
   ```bash
   cp .env.example .env
   # Edit .env with your settings - see .env.example for all options
   ```

   **Note**: The system works without API keys for basic price monitoring. API keys are only needed for:
   - Enhanced Coinmate features (account balance, trading)
   - Kraken private endpoints (if implementing actual trading)

## Usage

### Quick Start with Makefile

The easiest way to get started:

```bash
# Show all available commands
make help

# Quick development setup (install + format + test + run)
make dev

# Just run the monitor (auto-starts database if enabled)
make run

# Run without database for lightweight monitoring
DATABASE_ENABLED=false make run
```

### Basic Monitoring

Run the Bitcoin arbitrage monitor:

```bash
# Using Makefile (recommended)
make run

# Or directly with uv
uv run python main.py
```

**Sample Output:**
```
[2025-06-08 06:23:15] Starting Bitcoin Latency Arbitrage POC...
[2025-06-08 06:23:15] Monitoring exchanges: ['kraken', 'coinmate']
[2025-06-08 06:23:15] Trading symbol: BTC/USDT
[2025-06-08 06:23:15] Minimum profit threshold: 0.1%
[2025-06-08 06:23:15] --------------------------------------------------
[2025-06-08 06:23:15] ✓ Initialized kraken
[2025-06-08 06:23:15] ✓ Initialized coinmate
[2025-06-08 06:23:16] ✓ Telegram notifications enabled
[2025-06-08 06:23:16] ✓ Telegram connection test successful
[2025-06-08 06:23:17] ✓ Updated exchange rates (CZK/USD: 0.0417)
[2025-06-08 06:23:18] ✓ Kraken API: BTC/USD = 105589.40 USD ($105,589.40 USD)
[2025-06-08 06:23:18] ✓ Coinmate API: BTC/CZK = 2295278.00 CZK ($105,724.46 USD)

[2025-06-08 06:23:18] Active exchanges (2/2): kraken, coinmate
[2025-06-08 06:23:18] Current spread: $135.06 (0.13%)
[2025-06-08 06:23:18] Lowest: kraken - $105,589.40 USD
[2025-06-08 06:23:18] Highest: coinmate - $105,724.46 USD
```

### Configuration

Edit `config/settings.py` or set environment variables in `.env`:

```python
# Minimum profit threshold (percentage)
# Telegram alerts will be sent for all opportunities above this threshold
MIN_PROFIT_PERCENTAGE = 0.1
```

### Environment Variables

Copy `.env.example` to `.env` and configure as needed:

```bash
cp .env.example .env
```

**Core Settings:**
```bash
# Minimum profit threshold for detection
MIN_PROFIT_PERCENTAGE=0.1

# Trading fee configuration (percentage)
KRAKEN_TRADING_FEE=0.26
COINMATE_TRADING_FEE=0.35
DEFAULT_TRADING_FEE=0.25

# Enable dynamic fee fetching from exchange APIs
# Note: Coinmate fee fetching requires API credentials
DYNAMIC_FEES_ENABLED=false
```

**Telegram Notifications (Optional):**
```bash
# Enable/disable Telegram notifications entirely
TELEGRAM_ENABLED=true
# Get from @BotFather
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789
# Note: Telegram alerts use the same threshold as MIN_PROFIT_PERCENTAGE
# When TELEGRAM_ENABLED=false, enhanced logging shows why notifications are disabled
```

**Exchange API Keys (Optional):**
```bash
# Kraken (for private endpoints)
KRAKEN_API_KEY=your_kraken_api_key
KRAKEN_SECRET_KEY=your_kraken_secret_key

# Coinmate (for account balance, trading, etc.)
COINMATE_API_KEY=your_coinmate_api_key
COINMATE_SECRET_KEY=your_coinmate_secret_key
COINMATE_CLIENT_ID=your_coinmate_client_id
```

**Database Configuration (Optional):**
```bash
# Enable/disable TimescaleDB for historical data storage
# System works perfectly without database - just loses historical data
DATABASE_ENABLED=true
# Database connection settings (configurable)
DATABASE_HOST=localhost
DATABASE_PORT=5433
DATABASE_NAME=arbitrage
DATABASE_USER=arbitrage_user
DATABASE_PASSWORD=arbitrage_pass
# PostgreSQL connection URL for TimescaleDB (auto-constructed from above)
# Or override with custom URL: postgresql://user:pass@host:port/database
DATABASE_URL=postgresql://arbitrage_user:arbitrage_pass@localhost:5433/arbitrage
# Data retention period in days
DB_RETENTION_DAYS=30
# Timezone for displaying timestamps in database queries
TIMEZONE=UTC
```

**Note:** Basic price monitoring works without any configuration!

## 📱 Telegram Notifications Setup

Get instant alerts when profitable arbitrage opportunities are detected!

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Choose a name and username for your bot
4. Copy the bot token (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Get Your Chat ID

1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":123456789}` in the response
4. Copy the chat ID number

### 3. Configure Environment Variables

Add to your `.env` file:

```bash
# Enable/disable Telegram notifications
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789
# Telegram alerts are sent for all detected opportunities
```

### 4. Test Your Setup

```bash
# Test Telegram integration manually
make telegram-test
# Or: uv run python tests/integration/test_telegram.py

# Or let the application test automatically on startup
make run
# Or: uv run python main.py
```

### Sample Alert Message

```
🚨 Arbitrage Opportunity Detected!

💰 Profit: $127.45 (0.85%)
📈 Buy: coinmate @ $42,350.00
📉 Sell: kraken @ $42,477.45
📊 Volume Limit: 2.5000 BTC

⚡ Act quickly - prices change rapidly!
```

**Note:** When `TELEGRAM_ENABLED=false`, the system provides enhanced console logging showing:
- Detailed fee calculations for each exchange
- Reasons why Telegram notifications are disabled
- All arbitrage opportunities are still detected and logged

## 📊 TimescaleDB Integration (Optional)

The system includes optional TimescaleDB integration for historical data storage and advanced analytics.

### Features

- **Completely Optional**: System works perfectly without database
- **Auto-Start**: `make run` automatically starts TimescaleDB container if enabled
- **Graceful Fallback**: Continues monitoring if database connection fails
- **Time-Series Optimized**: Hypertables for efficient price data storage
- **Real-Time Analytics**: Built-in views and functions for analysis

### Quick Start

```bash
# Enable database and run (auto-starts TimescaleDB container)
make run

# Manually start database
make db-up

# Connect to database with timezone support (recommended)
make db-connect

# Or connect directly (shows UTC timestamps)
docker exec -it $(docker ps -q --filter "name=timescaledb") psql -U arbitrage_user -d arbitrage

# View stored data
SELECT * FROM get_latest_prices();
```

### Database Operations

```bash
# Database management
make db-up          # Start TimescaleDB container
make db-down        # Stop TimescaleDB
make db-logs        # View database logs
make db-reset       # Reset database (destructive!)
make db-test        # Run database integration tests

# Database access with timezone support
make db-connect     # Connect to database with local timezone
make db-timezone    # Set database default timezone from .env

# Run without database
DATABASE_ENABLED=false make run
```

### What Gets Stored

1. **Price Data**: All fetched prices with timestamps
2. **Arbitrage Opportunities**: Detected profitable opportunities
3. **Exchange Health**: API response times and error tracking
4. **Analytics Views**: Pre-computed spreads and summaries

### Sample Queries

```sql
-- Recent arbitrage opportunities (in your local timezone)
SELECT buy_exchange, sell_exchange, profit_percentage, profit_usd, local_timestamp
FROM arbitrage_opportunities_local 
WHERE utc_timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY profit_percentage DESC;

-- Exchange prices (in your local timezone)
SELECT exchange_name, price_usd, local_timestamp, utc_timestamp
FROM exchange_prices_local 
ORDER BY local_timestamp DESC LIMIT 10;

-- Price spread history
SELECT * FROM get_price_spread_history(24);

-- Exchange performance
SELECT exchange_name, COUNT(*) as requests, 
       AVG(response_time_ms) as avg_response_time
FROM exchange_status 
WHERE timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY exchange_name;
```

### Disable Database

Set `DATABASE_ENABLED=false` in `.env` or environment variable to run lightweight monitoring without any database dependencies.

## 📊 Grafana Monitoring (Optional)

The system includes optional Grafana integration for visual monitoring and analytics dashboards.

### Features

- **Real-time dashboards**: Live Bitcoin arbitrage monitoring
- **Historical analysis**: Price trends and opportunity tracking
- **Exchange performance**: API response times and health monitoring
- **Profit analytics**: Opportunity frequency and profitability metrics

### Quick Start

```bash
# Start full monitoring stack (TimescaleDB + Grafana)
docker-compose -f docker-compose.grafana.yml up -d

# Access Grafana dashboard
open http://localhost:3000
# Default login: admin/admin
```

### Dashboard Features

The included Bitcoin Arbitrage dashboard provides:
- Real-time price differences between exchanges
- Historical arbitrage opportunities
- Exchange health and response times
- Profit potential analysis

### Configuration

```bash
# Configure Grafana datasource
# Edit grafana/datasources/timescaledb.yml with your database settings

# Customize dashboards
# Edit grafana/dashboards/bitcoin-arbitrage.json
```

## 📓 Jupyter Notebooks (Optional)

Data analysis notebooks are included for deeper market analysis and backtesting.

### Setup

```bash
# Start Jupyter notebook server
docker-compose -f docker-compose.jupyter.yml up -d

# Access Jupyter
open http://localhost:8888
```

### Available Notebooks

1. **arbitrage_analysis.ipynb**: Comprehensive market analysis
   - Historical arbitrage opportunity analysis
   - Price spread trends and patterns
   - Exchange performance comparison
   - Profit potential modeling

### Analysis Features

- Historical data visualization
- Statistical analysis of arbitrage opportunities
- Market trend identification
- Exchange comparison metrics

## Project Structure

### Current Structure

```
exchange-price-slippage-arbitrage/
├── src/
│   ├── __init__.py
│   ├── apis/                      # External API integrations
│   │   ├── __init__.py
│   │   ├── base_exchange.py          # Abstract base class for exchanges
│   │   ├── coinmate_api.py           # Coinmate API implementation
│   │   └── kraken_api.py             # Kraken API implementation
│   ├── core/                      # Core business logic
│   │   ├── __init__.py
│   │   ├── arbitrage_detector.py     # Arbitrage opportunity detection
│   │   ├── data_models.py            # Shared data classes
│   │   └── exchange_monitor.py       # Real-time price monitoring
│   ├── services/                  # Business services
│   │   ├── __init__.py
│   │   ├── currency_converter.py     # USD/CZK conversion
│   │   ├── database_service.py       # TimescaleDB integration
│   │   └── telegram_service.py       # Telegram notifications
│   └── utils/                     # Shared utilities
│       ├── __init__.py
│       └── logging.py                # Logging utilities
├── config/                        # Configuration files
│   ├── __init__.py
│   └── settings.py                   # Configuration settings
├── sql/                           # Database schema and migrations
│   └── init.sql                      # TimescaleDB initialization
├── tests/                         # Comprehensive test suite (100+ tests)
│   ├── __init__.py
│   ├── conftest.py                   # Shared test fixtures
│   ├── test_runner.py                # Test runner script
│   ├── unit/                         # Unit tests
│   │   ├── test_arbitrage_detector.py
│   │   ├── test_base_exchange.py        # Tests for base exchange class
│   │   ├── test_coinmate_api.py
│   │   ├── test_currency_converter.py
│   │   ├── test_database_service.py     # Database service tests
│   │   ├── test_kraken_api.py
│   │   └── test_telegram_service.py
│   └── integration/                  # Integration tests
│       ├── test_database_integration.py  # Database tests
│       └── test_telegram.py             # Telegram API tests
├── grafana/                       # Grafana monitoring setup
│   ├── dashboards/
│   │   ├── bitcoin-arbitrage.json       # Bitcoin arbitrage dashboard
│   │   └── dashboard.yml                # Dashboard configuration
│   └── datasources/
│       └── timescaledb.yml              # TimescaleDB datasource config
├── notebooks/                     # Jupyter notebooks for analysis
│   └── arbitrage_analysis.ipynb         # Data analysis notebook
├── monitoring/                    # Monitoring and logging
│   └── logrotate.conf                # Log rotation configuration
├── data/                          # Data directory (created at runtime)
├── logs/                          # Application logs (created at runtime)
├── coinmate_signature.py          # Coinmate API signature utility
├── .env.example                   # Environment variables template
├── CLAUDE.md                      # AI assistant instructions
├── Dockerfile                     # Docker container definition
├── docker-compose.yml             # Docker Compose + TimescaleDB
├── docker-compose.grafana.yml     # Grafana monitoring stack
├── docker-compose.jupyter.yml     # Jupyter notebook setup
├── deploy.sh                      # Simple deployment script
├── jupyter-requirements.txt       # Jupyter notebook dependencies
├── Makefile                       # Development commands
├── main.py                        # Main application entry point
├── pyproject.toml                 # UV project configuration
├── uv.lock                        # UV lock file
└── README.md                      # This file
```

**Benefits of this structure:**
- **Clear separation of concerns**: APIs, core logic, and utilities are isolated  
- **Polymorphic design**: Abstract base class allows easy exchange expansion
- **Database integration**: Optional TimescaleDB with full schema management
- **Monitoring & Analytics**: Grafana dashboards and Jupyter notebooks for analysis
- **Scalability**: Easy to add new exchanges via BaseExchangeAPI interface
- **Maintainability**: Related files grouped together
- **Testing organization**: Tests mirror source structure with comprehensive coverage
- **Configuration management**: All config in dedicated directory
- **Documentation**: Comprehensive docs with SQL examples and AI instructions

## Supported Exchanges

### International Exchange
- **Kraken** - BTC/USD trading pair via dedicated API

### Czech Exchange  
- **Coinmate** - BTC/CZK trading pair via dedicated API

### Currency Support
- **USD** - Base currency for comparisons
- **CZK** - Converted to USD via live exchange rates

### Adding More Exchanges

The polymorphic architecture supports easy expansion:
1. Add exchange to `config/settings.py` 
2. Specify trading pair in `EXCHANGE_TRADING_PAIRS`
3. Create API client inheriting from `BaseExchangeAPI` in `src/apis/`
4. Implement required abstract methods: `get_ticker()`, `normalize_pair()`, etc.
5. Add factory support in `create_exchange_api()` function
6. The system automatically uses the new exchange via polymorphism

## 🚀 Production Deployment

For continuous monitoring on your homeserver, deploy with Docker:

### Quick Deployment

```bash
# Using Makefile (recommended)
make docker-deploy

# Or directly
./deploy.sh
```

The deployment script will:
- ✅ Check Docker installation
- ✅ Create necessary directories
- ✅ Help you configure environment variables
- ✅ Build and start the service
- ✅ Show you management commands

### Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose installed
- Git installed

```bash
# Install Docker and Docker Compose (if not already installed)
sudo apt update
sudo apt install docker.io docker-compose git
sudo usermod -aG docker $USER
# Log out and back in to apply group changes
```

### Production Configuration

#### API Key Setup

1. **Kraken API**: Visit https://kraken.com/u/security/api
   - Create read-only key for monitoring
   - Enable "Query Funds" and "Query Open Orders" if needed

2. **Coinmate API**: Visit https://coinmate.io/api
   - Create API key with minimal permissions
   - Only enable "Account info" for monitoring

#### Environment Variables for Production

Edit `.env` file with your settings:

```bash
# Required
MIN_PROFIT_PERCENTAGE=0.1

# Trading fee configuration (percentage)
# These are the default trading fees for each exchange
KRAKEN_TRADING_FEE=0.26
COINMATE_TRADING_FEE=0.35
DEFAULT_TRADING_FEE=0.25

# Enable dynamic fee fetching from exchange APIs
# When enabled, tries to fetch real-time fees, falls back to configured values
DYNAMIC_FEES_ENABLED=false

# Telegram notifications
# Set to false to disable Telegram notifications entirely
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Optional API keys for enhanced features
KRAKEN_API_KEY=your_key_here
KRAKEN_SECRET_KEY=your_secret_here
COINMATE_API_KEY=your_key_here
COINMATE_SECRET_KEY=your_secret_here
COINMATE_CLIENT_ID=your_id_here

# Development
SANDBOX_MODE=false  # Set to false for production
```

### Monitoring & Maintenance

#### Essential Management Commands

```bash
# View live logs
docker-compose logs -f

# View recent logs
docker-compose logs --tail=50

# Restart service
docker-compose restart

# Stop service
docker-compose down

# Update and restart
git pull && docker-compose build && docker-compose up -d

# Check container status
docker-compose ps

# Access container shell
docker-compose exec arbitrage-monitor bash
```

#### Log Management

Logs are automatically rotated using logrotate:

```bash
# Install logrotate config (optional - run once)
sudo cp monitoring/logrotate.conf /etc/logrotate.d/bitcoin-arbitrage

# Test logrotate
sudo logrotate -d /etc/logrotate.d/bitcoin-arbitrage
```

#### Health Monitoring

Create a simple health check script:

```bash
#!/bin/bash
# health-check.sh

if docker-compose ps | grep -q "Up"; then
    echo "✅ Service is running"
    exit 0
else
    echo "❌ Service is down - restarting..."
    docker-compose up -d
    exit 1
fi
```

Add to crontab for automated monitoring:

```bash
# Add to crontab (crontab -e)
*/5 * * * * cd /path/to/your/project && ./health-check.sh >> logs/health.log 2>&1
```

### Troubleshooting

#### Common Issues

1. **Service won't start**
   ```bash
   # Check logs
   docker-compose logs
   ```

2. **API connection errors**
   - Verify API keys in `.env`
   - Check network connectivity
   - Ensure exchange APIs are accessible

3. **High memory usage**
   - Check for memory leaks in logs
   - Restart service: `docker-compose restart`

4. **Permission errors**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER logs/
   ```

#### Performance Tuning

Add resource limits by editing `docker-compose.yml`:

```yaml
services:
  arbitrage-monitor:
    # ... other config
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

### Security Considerations

1. **API Keys**
   - Use read-only keys when possible
   - Set IP restrictions on exchange APIs
   - Store keys securely in `.env` file

2. **Network Security**
   - Run behind firewall
   - Consider VPN for sensitive operations
   - Monitor outbound connections

3. **System Security**
   - Run as non-root user
   - Regular security updates
   - Monitor system logs

### Updates

#### Automatic Updates

```bash
# Create update script in your project directory
cat > auto-update.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
git pull
docker-compose build
docker-compose up -d
EOF
chmod +x auto-update.sh

# Add to crontab for weekly updates
0 2 * * 0 /path/to/your/project/auto-update.sh >> logs/update.log 2>&1
```

#### Manual Updates

```bash
# Simple update
git pull
docker-compose build
docker-compose up -d
```

### Scaling & Optimization

1. **Multiple Exchanges**
   - Add new exchanges to `config/settings.py`
   - Update `EXCHANGE_TRADING_PAIRS`

2. **Performance Monitoring**
   - Monitor CPU/memory usage
   - Track API response times
   - Log arbitrage opportunities

3. **Data Storage**
   - Consider logging to database
   - Implement data retention policies
   - Add backup strategies

## Risk Warnings

⚠️ **Important Disclaimers:**

1. **This is a POC**: This project is for educational and research purposes only
2. **Market Risks**: Cryptocurrency trading involves significant financial risk
3. **Execution Risk**: Arbitrage opportunities may disappear before execution
4. **Regulatory Risk**: Ensure compliance with local regulations
5. **Technical Risk**: Always test in sandbox mode first

## Development

### Running Tests

The project includes a comprehensive test suite with 100+ tests:

```bash
# Using Makefile (recommended)
make test                    # Run all tests
make test-unit              # Run only unit tests (76 tests)
make test-integration       # Run integration tests
make test-coverage          # Run with coverage report
make telegram-test          # Test Telegram integration
make db-test                # Test database integration

# Quick pre-commit checks
make check                  # format + lint + unit tests
make ci                     # full CI pipeline

# Or use direct commands
uv run pytest              # Run all tests
uv run python tests/test_runner.py unit          # Run only unit tests
uv run python tests/test_runner.py integration   # Run integration tests
uv run python tests/test_runner.py coverage      # Run with coverage report

# Run with verbose output
uv run python tests/test_runner.py unit -v

# Run specific test files
uv run pytest tests/unit/test_coinmate_api.py
uv run pytest tests/unit/test_telegram_service.py

# Show test runner help
uv run python tests/test_runner.py
```

### Test Categories
- **Unit tests** (`@pytest.mark.unit`) - Fast, isolated component tests
- **Integration tests** (`@pytest.mark.integration`) - Component interaction tests  
- **Slow tests** (`@pytest.mark.slow`) - Real API calls (optional)

### Code Formatting

```bash
# Using Makefile (recommended)
make format                 # Format code with black
make fix                    # Auto-fix imports, sort, and format
make lint                   # Lint code with flake8 (100 char limit)
make clean                  # Clean cache and temp files

# Quick workflows
make check                  # Auto-fix + lint + unit tests
make ci                     # Full CI pipeline

# Or directly
uv run black .
uv run autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive .
uv run isort .
uv run flake8 .
```

## Dependencies

### Core Dependencies
- **aiohttp**: Async HTTP client (Kraken API, Coinmate API, currency conversion)
- **asyncpg**: Async PostgreSQL driver for TimescaleDB integration
- **python-dotenv**: Environment variable management
- **numpy/pandas**: Data analysis and manipulation
- **requests/websocket-client**: HTTP and WebSocket support

### Development Dependencies  
- **pytest**: Testing framework with async support
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **aioresponses**: HTTP request mocking
- **black/flake8**: Code formatting and linting

### Key Features
- **Multi-currency support**: USD, CZK conversion
- **Native APIs**: Direct Kraken and Coinmate API clients with abstract base class
- **TimescaleDB integration**: Optional time-series database for analytics
- **Real-time data**: Live exchange rates and price monitoring
- **Comprehensive testing**: 100+ tests covering all components including database

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is for educational purposes. Please ensure compliance with all applicable laws and exchange terms of service.

## Disclaimer

This software is provided "as is" without warranty. The authors are not responsible for any financial losses incurred through the use of this software. Always conduct thorough testing and risk assessment before any live trading.