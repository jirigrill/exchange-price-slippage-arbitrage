"""
Tests for the base exchange API interface.
"""

from unittest.mock import MagicMock

import pytest

from src.apis.base_exchange import BaseExchangeAPI, create_exchange_api


class MockExchangeAPI(BaseExchangeAPI):
    """Mock implementation for testing"""

    def __init__(self, api_key=None, api_secret=None, **kwargs):
        super().__init__(api_key, api_secret, **kwargs)
        self.session = None

    async def __aenter__(self):
        self.session = MagicMock()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session = None

    async def get_ticker(self, pair: str):
        return {"price": 50000.0, "volume": 1.5}

    async def get_trading_fees(self, pair: str):
        return 0.25

    def normalize_pair(self, pair: str) -> str:
        return pair.replace("/", "_")

    def get_exchange_name(self) -> str:
        return "mock"

    def _generate_signature(self, *args, **kwargs) -> str:
        return "mock_signature"

    async def _make_request(self, endpoint: str, method: str = "GET", **kwargs):
        return {"result": "success"}


@pytest.mark.unit
class TestBaseExchangeAPI:

    def test_init_without_credentials(self):
        """Test initialization without API credentials"""
        api = MockExchangeAPI()

        assert api.api_key is None
        assert api.api_secret is None
        assert api.session is None
        assert not api.is_authenticated()

    def test_init_with_credentials(self):
        """Test initialization with API credentials"""
        api = MockExchangeAPI("test_key", "test_secret")

        assert api.api_key == "test_key"
        assert api.api_secret == "test_secret"
        assert api.is_authenticated()

    def test_init_with_kwargs(self):
        """Test initialization with additional kwargs"""
        api = MockExchangeAPI("key", "secret", client_id="test_client")

        assert api.api_key == "key"
        assert api.api_secret == "secret"
        assert api.is_authenticated()

    async def test_context_manager(self):
        """Test async context manager functionality"""
        api = MockExchangeAPI()

        async with api as ctx_api:
            assert ctx_api is api
            assert api.session is not None

        # Session should be cleaned up
        assert api.session is None

    async def test_required_methods(self):
        """Test that required abstract methods are implemented"""
        api = MockExchangeAPI()

        # Test ticker
        ticker = await api.get_ticker("BTC/USD")
        assert ticker == {"price": 50000.0, "volume": 1.5}

        # Test trading fees
        fees = await api.get_trading_fees("BTC/USD")
        assert fees == 0.25

        # Test normalization
        assert api.normalize_pair("BTC/USD") == "BTC_USD"

        # Test exchange name
        assert api.get_exchange_name() == "mock"

        # Test signature generation
        assert api._generate_signature() == "mock_signature"

        # Test request making
        result = await api._make_request("test")
        assert result == {"result": "success"}

    async def test_optional_methods(self):
        """Test that optional methods return None by default"""
        api = MockExchangeAPI()

        assert await api.get_orderbook("BTC/USD") is None
        assert await api.get_recent_trades("BTC/USD") is None
        assert await api.get_balance() is None

    def test_is_authenticated(self):
        """Test authentication status checking"""
        # No credentials
        api1 = MockExchangeAPI()
        assert not api1.is_authenticated()

        # Only API key
        api2 = MockExchangeAPI("key", None)
        assert not api2.is_authenticated()

        # Only secret
        api3 = MockExchangeAPI(None, "secret")
        assert not api3.is_authenticated()

        # Both credentials
        api4 = MockExchangeAPI("key", "secret")
        assert api4.is_authenticated()


@pytest.mark.unit
class TestExchangeFactory:

    def test_create_kraken_api(self):
        """Test creating Kraken API instance"""
        api = create_exchange_api(
            "kraken", api_key="test_key", api_secret="test_secret"
        )

        assert api.__class__.__name__ == "KrakenAPI"
        assert api.api_key == "test_key"
        assert api.api_secret == "test_secret"
        assert api.get_exchange_name() == "kraken"

    def test_create_coinmate_api(self):
        """Test creating Coinmate API instance"""
        api = create_exchange_api(
            "coinmate",
            api_key="test_key",
            api_secret="test_secret",
            client_id="test_client",
        )

        assert api.__class__.__name__ == "CoinmateAPI"
        assert api.api_key == "test_key"
        assert api.api_secret == "test_secret"
        assert api.client_id == "test_client"
        assert api.get_exchange_name() == "coinmate"

    def test_case_insensitive_exchange_names(self):
        """Test that exchange names are case insensitive"""
        api1 = create_exchange_api("KRAKEN")
        api2 = create_exchange_api("Kraken")
        api3 = create_exchange_api("kraken")

        assert all(api.get_exchange_name() == "kraken" for api in [api1, api2, api3])

    def test_unsupported_exchange(self):
        """Test error handling for unsupported exchanges"""
        with pytest.raises(ValueError, match="Unsupported exchange: binance"):
            create_exchange_api("binance")

    def test_factory_with_no_credentials(self):
        """Test factory function without credentials"""
        api = create_exchange_api("kraken")

        assert api.api_key is None
        assert api.api_secret is None
        assert not api.is_authenticated()


@pytest.mark.unit
class TestPolymorphism:
    """Test that APIs can be used polymorphically"""

    async def test_polymorphic_usage(self):
        """Test that different APIs can be used through base interface"""
        from src.apis.coinmate_api import CoinmateAPI
        from src.apis.kraken_api import KrakenAPI

        apis = [
            KrakenAPI("key1", "secret1"),
            CoinmateAPI("key2", "secret2", "client_id"),
            MockExchangeAPI("key3", "secret3"),
        ]

        for api in apis:
            # All should implement the base interface
            assert isinstance(api, BaseExchangeAPI)
            assert api.is_authenticated()
            assert isinstance(api.get_exchange_name(), str)
            assert isinstance(api.normalize_pair("BTC/USD"), str)

    def test_pair_normalization_differences(self):
        """Test that different exchanges normalize pairs differently"""
        from src.apis.coinmate_api import CoinmateAPI
        from src.apis.kraken_api import KrakenAPI

        kraken = KrakenAPI()
        coinmate = CoinmateAPI()

        # Different exchanges should normalize differently
        assert kraken.normalize_pair("BTC/USD") == "BTCUSD"
        assert coinmate.normalize_pair("BTC/USD") == "BTC_USD"
