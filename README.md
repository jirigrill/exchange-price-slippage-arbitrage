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
- ✅ **Fee Accounting**: Trading fees included in profit calculations
- ✅ **Telegram Notifications**: Instant alerts for profitable opportunities
- ✅ **Async Architecture**: Efficient concurrent price monitoring
- ✅ **Comprehensive Testing**: Full pytest suite with 53 tests
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
   uv sync
   ```

3. **Configure environment variables (optional)**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys if needed
   ```

   **Note**: The system works without API keys for basic price monitoring. API keys are only needed for:
   - Enhanced Coinmate features (account balance, trading)
   - Kraken private endpoints (if implementing actual trading)

## Usage

### Basic Monitoring

Run the Bitcoin arbitrage monitor:

```bash
uv run python main.py
```

**Sample Output:**
```
Starting Bitcoin Latency Arbitrage POC...
Monitoring exchanges: ['kraken', 'coinmate']
Trading symbol: BTC/USDT
Minimum profit threshold: 0.1%
--------------------------------------------------
✓ Initialized kraken
✓ Initialized coinmate
✓ Updated exchange rates (CZK/USD: 0.0417)
✓ Kraken API: BTC/USD = 105589.40 USD ($105,589.40 USD)
✓ Coinmate API: BTC/CZK = 2295278.00 CZK ($105,724.46 USD)

Active exchanges (2/2): kraken, coinmate
Current spread: $135.06 (0.13%)
Lowest: kraken - $105,589.40 USD
Highest: coinmate - $105,724.46 USD
```

### Configuration

Edit `config/settings.py` or set environment variables in `.env`:

```python
# Minimum profit threshold (percentage)
MIN_PROFIT_PERCENTAGE = 0.1

# Telegram alert threshold (percentage)
TELEGRAM_ALERT_THRESHOLD = 0.5
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
```

**Telegram Notifications (Optional):**
```bash
# Get from @BotFather
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789
TELEGRAM_ALERT_THRESHOLD=0.5  # Send alerts for profits >= 0.5%
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
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789
TELEGRAM_ALERT_THRESHOLD=0.5  # Send alerts for profits >= 0.5%
```

### 4. Test Your Setup

The application will automatically test the Telegram connection on startup and send you a test message.

### Sample Alert Message

```
🚨 Arbitrage Opportunity Detected!

💰 Profit: $127.45 (0.85%)
📈 Buy: coinmate @ $42,350.00
📉 Sell: kraken @ $42,477.45
📊 Volume Limit: 2.5000 BTC

⚡ Act quickly - prices change rapidly!
```

## Project Structure

### Current Structure

```
├── src/
│   ├── core/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── arbitrage_detector.py  # Arbitrage opportunity detection
│   │   └── exchange_monitor.py    # Real-time price monitoring
│   ├── apis/                   # External API integrations
│   │   ├── __init__.py
│   │   ├── coinmate_api.py        # Dedicated Coinmate API client
│   │   └── kraken_api.py          # Dedicated Kraken API client
│   ├── services/               # Business services
│   │   ├── __init__.py
│   │   ├── currency_converter.py  # USD/CZK conversion
│   │   └── telegram_service.py    # Telegram notifications
│   └── utils/                  # Shared utilities
│       ├── __init__.py
│       └── logging.py             # Logging utilities
├── config/                     # Configuration files
│   ├── __init__.py
│   └── settings.py             # Configuration settings
├── tests/                      # Comprehensive test suite
│   ├── unit/                   # Unit tests
│   │   ├── conftest.py        # Shared test fixtures
│   │   ├── test_arbitrage_detector.py
│   │   ├── test_coinmate_api.py
│   │   ├── test_kraken_api.py
│   │   └── test_currency_converter.py
│   └── integration/            # Integration tests
├── monitoring/                 # Monitoring and logging
│   └── logrotate.conf         # Log rotation configuration
├── docs/                       # Documentation
│   └── DEPLOYMENT.md          # Deployment guide
├── Dockerfile                  # Docker container definition
├── docker-compose.yml          # Docker Compose configuration
├── deploy.sh                   # Simple deployment script
├── main.py                     # Main application entry point
├── test_runner.py              # Test runner script
├── pyproject.toml              # UV project configuration
└── README.md                   # This file
```

**Benefits of this structure:**
- **Clear separation of concerns**: APIs, core logic, and utilities are isolated
- **Scalability**: Easy to add new exchanges in `apis/` directory
- **Maintainability**: Related files grouped together
- **Testing organization**: Tests mirror source structure
- **Configuration management**: All config in dedicated directory

## Supported Exchanges

### International Exchange
- **Kraken** - BTC/USD trading pair via dedicated API

### Czech Exchange  
- **Coinmate** - BTC/CZK trading pair via dedicated API

### Currency Support
- **USD** - Base currency for comparisons
- **CZK** - Converted to USD via live exchange rates

### Adding More Exchanges

The architecture supports easy expansion:
1. Add exchange to `config/settings.py` 
2. Specify trading pair in `EXCHANGE_TRADING_PAIRS`
3. Create custom API client in `src/apis/` directory
4. Add support in `ExchangeMonitor.fetch_price()` method

## 🚀 Production Deployment

For continuous monitoring on your homeserver, deploy with Docker:

```bash
./deploy.sh
```

This includes:
- ✅ Automatic restarts on failure
- ✅ Log rotation and monitoring  
- ✅ Health checks
- ✅ Resource limits
- ✅ Security hardening

See [**DEPLOYMENT.md**](docs/DEPLOYMENT.md) for detailed setup guide.

## Risk Warnings

⚠️ **Important Disclaimers:**

1. **This is a POC**: This project is for educational and research purposes only
2. **Market Risks**: Cryptocurrency trading involves significant financial risk
3. **Execution Risk**: Arbitrage opportunities may disappear before execution
4. **Regulatory Risk**: Ensure compliance with local regulations
5. **Technical Risk**: Always test in sandbox mode first

## Development

### Running Tests

The project includes a comprehensive test suite with 53 tests:

```bash
# Run all tests
uv run pytest

# Run only unit tests (fast)
python test_runner.py unit

# Run with verbose output
python test_runner.py unit -v

# Run specific test file
uv run pytest tests/test_coinmate_api.py

# Run with coverage
python test_runner.py coverage
```

### Test Categories
- **Unit tests** (`@pytest.mark.unit`) - Fast, isolated component tests
- **Integration tests** (`@pytest.mark.integration`) - Component interaction tests  
- **Slow tests** (`@pytest.mark.slow`) - Real API calls (optional)

### Code Formatting

```bash
uv run black .
uv run flake8 .
```

## Dependencies

### Core Dependencies
- **aiohttp**: Async HTTP client (Kraken API, Coinmate API, currency conversion)
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
- **Native APIs**: Direct Kraken and Coinmate API clients (no third-party dependencies)
- **Real-time data**: Live exchange rates and price monitoring
- **Comprehensive testing**: 53 tests covering all components

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