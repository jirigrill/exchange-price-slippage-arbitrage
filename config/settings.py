import os

from dotenv import load_dotenv

load_dotenv()

LARGE_EXCHANGES = ["kraken"]

SMALL_EXCHANGES = ["coinmate"]

ALL_EXCHANGES = LARGE_EXCHANGES + SMALL_EXCHANGES

# Default trading symbol
TRADING_SYMBOL = "BTC/USDT"

# Exchange-specific trading pairs
EXCHANGE_TRADING_PAIRS = {"coinmate": "BTC/CZK", "kraken": "BTC/USD"}

MIN_PROFIT_PERCENTAGE = float(os.getenv("MIN_PROFIT_PERCENTAGE", "0.1"))

# Trading fee configuration (percentage)
KRAKEN_TRADING_FEE = float(os.getenv("KRAKEN_TRADING_FEE", "0.26"))
COINMATE_TRADING_FEE = float(os.getenv("COINMATE_TRADING_FEE", "0.35"))
DEFAULT_TRADING_FEE = float(os.getenv("DEFAULT_TRADING_FEE", "0.25"))

# Enable dynamic fee fetching from exchange APIs
DYNAMIC_FEES_ENABLED = os.getenv("DYNAMIC_FEES_ENABLED", "false").lower() == "true"

# Telegram notification settings
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "true").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Telegram notifications will use the same threshold as MIN_PROFIT_PERCENTAGE
# No separate threshold needed - alert on every detected opportunity

# Database configuration
# Can be overridden by DATABASE_ENABLED environment variable
DATABASE_ENABLED = os.getenv("DATABASE_ENABLED", "true").lower() == "true"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://arbitrage_user:arbitrage_pass@localhost:5432/arbitrage",
)

# Database is optional - system works without it but loses historical data and analytics
# Set DATABASE_ENABLED=false in .env or via environment to disable completely

# Database settings
DB_RETENTION_DAYS = int(os.getenv("DB_RETENTION_DAYS", "30"))
DB_BATCH_SIZE = int(os.getenv("DB_BATCH_SIZE", "100"))

# Timezone configuration for database timestamp display
# Data is always stored in UTC, but this controls how timestamps are displayed in queries
TIMEZONE = os.getenv("TIMEZONE", "UTC")


API_KEYS = {
    "kraken": {
        "apiKey": os.getenv("KRAKEN_API_KEY"),
        "secret": os.getenv("KRAKEN_SECRET_KEY"),
    },
    "coinmate": {
        "apiKey": os.getenv("COINMATE_API_KEY"),
        "secret": os.getenv("COINMATE_SECRET_KEY"),
        "clientId": os.getenv("COINMATE_CLIENT_ID"),
    },
}
