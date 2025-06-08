"""
Shared pytest fixtures for the arbitrage testing suite.
"""

import pytest

from src.core.exchange_monitor import PriceData
from src.services.currency_converter import CurrencyConverter


@pytest.fixture
def sample_btc_usd_price():
    """Sample BTC/USD price data from Kraken"""
    return PriceData(
        exchange="kraken",
        symbol="BTC/USD",
        price=102500.0,
        price_usd=102500.0,
        original_currency="USD",
        timestamp=1703254800.0,  # 2023-12-22 12:00:00 UTC
        volume=150.5,
    )


@pytest.fixture
def sample_btc_czk_price():
    """Sample BTC/CZK price data from Coinmate"""
    return PriceData(
        exchange="coinmate",
        symbol="BTC/CZK",
        price=2450000.0,
        price_usd=102083.33,  # Assuming 1 CZK = 0.0417 USD
        original_currency="CZK",
        timestamp=1703254800.0,
        volume=12.3,
    )


@pytest.fixture
def mock_coinmate_ticker_response():
    """Mock successful Coinmate API ticker response"""
    return {
        "error": False,
        "errorMessage": None,
        "data": {
            "last": 2450000.0,
            "high": 2460000.0,
            "low": 2440000.0,
            "amount": 12.3,
            "bid": 2449000.0,
            "ask": 2451000.0,
        },
    }


@pytest.fixture
def mock_coinmate_error_response():
    """Mock Coinmate API error response"""
    return {"error": True, "errorMessage": "Rate limit exceeded"}


@pytest.fixture
def mock_exchange_rates():
    """Mock exchange rates for currency conversion"""
    return {
        "CZK/USD": 0.0417,  # 1 CZK = 0.0417 USD (approx 24 CZK per USD)
        "USD/CZK": 24.0,
        "USDT/USD": 1.0,
        "USD/USDT": 1.0,
    }


@pytest.fixture
async def mock_currency_converter(mock_exchange_rates):
    """Mock currency converter with predefined rates"""
    converter = CurrencyConverter()
    converter.exchange_rates = mock_exchange_rates
    converter.last_update = 1703254800.0  # Mock recent update
    return converter


@pytest.fixture
def trading_pairs():
    """Standard trading pairs configuration"""
    return {"kraken": "BTC/USD", "coinmate": "BTC/CZK"}


@pytest.fixture
def api_keys():
    """Mock API keys configuration"""
    return {
        "kraken": {"apiKey": "test_kraken_key", "secret": "test_kraken_secret"},
        "coinmate": {
            "apiKey": "test_coinmate_key",
            "secret": "test_coinmate_secret",
            "clientId": "test_client_id",
        },
    }


@pytest.fixture
def arbitrage_opportunity_data():
    """Sample arbitrage opportunity data"""
    return {
        "buy_exchange": "coinmate",
        "sell_exchange": "kraken",
        "buy_price": 102083.33,
        "sell_price": 102500.0,
        "profit_usd": 416.67,
        "profit_percentage": 0.35,  # After fees
        "volume_limit": 12.3,
    }


# Scenario fixtures for different market conditions


@pytest.fixture
def bull_market_prices():
    """High price scenario"""
    return {"binance": 110000.0, "coinmate": 2640000.0}  # Higher CZK price


@pytest.fixture
def bear_market_prices():
    """Low price scenario"""
    return {"binance": 95000.0, "coinmate": 2280000.0}  # Lower CZK price


@pytest.fixture
def high_spread_scenario():
    """Scenario with significant price difference"""
    return {
        "kraken": 102500.0,  # Normal international price
        "coinmate": 2400000.0,  # Lower Czech price
    }


@pytest.fixture
def low_spread_scenario():
    """Scenario with minimal price difference"""
    return {
        "kraken": 102500.0,
        "coinmate": 2460000.0,  # Almost same price when converted
    }
