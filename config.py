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
