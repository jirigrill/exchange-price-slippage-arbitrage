"""
Tests for the Coinmate API client.
"""

from unittest.mock import patch

import pytest
from aioresponses import aioresponses

from src.apis.coinmate.api import CoinmateAPI, get_coinmate_btc_czk_price


@pytest.mark.unit
class TestCoinmateAPI:

    async def test_init_without_credentials(self):
        """Test API initialization without credentials"""
        api = CoinmateAPI()
        assert api.base_url == "https://coinmate.io/api"
        assert api.api_key is None
        assert api.api_secret is None
        assert api.client_id is None

    async def test_init_with_credentials(self):
        """Test API initialization with credentials"""
        api = CoinmateAPI("test_key", "test_secret", "test_client")
        assert api.api_key == "test_key"
        assert api.api_secret == "test_secret"
        assert api.client_id == "test_client"

    async def test_get_ticker_success(self, mock_coinmate_ticker_response):
        """Test successful ticker retrieval"""
        with aioresponses() as m:
            m.get(
                "https://coinmate.io/api/ticker?currencyPair=BTC_CZK",
                payload=mock_coinmate_ticker_response,
            )

            async with CoinmateAPI() as api:
                result = await api.get_ticker("BTC_CZK")

            assert result == mock_coinmate_ticker_response
            assert result["error"] is False
            assert result["data"]["last"] == 2450000.0

    async def test_get_ticker_error_response(self, mock_coinmate_error_response):
        """Test ticker retrieval with API error"""
        with aioresponses() as m:
            m.get(
                "https://coinmate.io/api/ticker?currencyPair=BTC_CZK",
                payload=mock_coinmate_error_response,
            )

            async with CoinmateAPI() as api:
                result = await api.get_ticker("BTC_CZK")

            assert result == mock_coinmate_error_response
            assert result["error"] is True
            assert "Rate limit" in result["errorMessage"]

    async def test_get_ticker_network_error(self):
        """Test ticker retrieval with network error"""
        with aioresponses() as m:
            m.get(
                "https://coinmate.io/api/ticker?currencyPair=BTC_CZK",
                exception=Exception("Network error"),
            )

            async with CoinmateAPI() as api:
                result = await api.get_ticker("BTC_CZK")

            assert result is None

    async def test_get_ticker_http_error(self):
        """Test ticker retrieval with HTTP error"""
        with aioresponses() as m:
            m.get("https://coinmate.io/api/ticker?currencyPair=BTC_CZK", status=500)

            async with CoinmateAPI() as api:
                result = await api.get_ticker("BTC_CZK")

            assert result is None

    async def test_get_orderbook_success(self):
        """Test successful orderbook retrieval"""
        mock_orderbook = {
            "error": False,
            "data": {
                "asks": [[2451000, 0.5], [2452000, 1.0]],
                "bids": [[2449000, 0.3], [2448000, 0.8]],
            },
        }

        with aioresponses() as m:
            m.get(
                "https://coinmate.io/api/orderBook?currencyPair=BTC_CZK",
                payload=mock_orderbook,
            )

            async with CoinmateAPI() as api:
                result = await api.get_orderbook("BTC_CZK")

            assert result == mock_orderbook
            assert len(result["data"]["asks"]) == 2
            assert len(result["data"]["bids"]) == 2

    async def test_get_trading_pairs_success(self):
        """Test successful trading pairs retrieval"""
        mock_pairs = {"error": False, "data": ["BTC_CZK", "ETH_CZK", "LTC_CZK"]}

        with aioresponses() as m:
            m.get("https://coinmate.io/api/tradingPairs", payload=mock_pairs)

            async with CoinmateAPI() as api:
                result = await api.get_trading_pairs()

            assert result == mock_pairs
            assert "BTC_CZK" in result["data"]

    @patch("time.time", return_value=1703254800)
    @patch("src.apis.coinmate.api.CoinmateAPI._generate_signature")
    async def test_authenticated_request(self, mock_signature, mock_time):
        """Test authenticated request creation"""
        mock_signature.return_value = "TEST_SIGNATURE"

        mock_balance = {"error": False, "data": {"BTC": 1.5, "CZK": 50000}}

        with aioresponses() as m:
            m.post("https://coinmate.io/api/balances", payload=mock_balance)

            async with CoinmateAPI("test_key", "test_secret", "test_client") as api:
                result = await api.get_balance()

            assert result == mock_balance
            mock_signature.assert_called_once()

    def test_generate_signature(self):
        """Test signature generation"""
        api = CoinmateAPI("test_key", "test_secret", "test_client")

        nonce = "1703254800000"

        signature = api._generate_signature(nonce)

        # Signature should be a hex string
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex length
        assert signature.isupper()  # Should be uppercase

    def test_generate_signature_no_secret(self):
        """Test signature generation without secret"""
        api = CoinmateAPI("test_key", None, "test_client")

        with pytest.raises(ValueError, match="Private key required"):
            api._generate_signature("123")

    @patch("time.time", return_value=1703254800)
    @patch("src.apis.coinmate.api.CoinmateAPI._generate_signature")
    async def test_get_trading_fees_success(self, mock_signature, mock_time):
        """Test successful trading fees retrieval"""
        mock_signature.return_value = "TEST_SIGNATURE"

        mock_fees_response = {
            "error": False,
            "data": {
                "maker": 0.35,
                "taker": 0.5,
                "timestamp": 1703254800
            }
        }

        with aioresponses() as m:
            m.post("https://coinmate.io/api/traderFees", payload=mock_fees_response)

            async with CoinmateAPI("test_key", "test_secret", "test_client") as api:
                result = await api.get_trading_fees("BTC_EUR")

            assert result == 0.5
            mock_signature.assert_called_once()

    @patch("time.time", return_value=1703254800)
    @patch("src.apis.coinmate.api.CoinmateAPI._generate_signature")
    async def test_get_trading_fees_pair_not_found(self, mock_signature, mock_time):
        """Test trading fees retrieval when currency pair is not found"""
        mock_signature.return_value = "TEST_SIGNATURE"

        mock_fees_response = {
            "error": False,
            "data": {
                "maker": 0.35,
                "timestamp": 1703254800
            }
        }

        with aioresponses() as m:
            m.post("https://coinmate.io/api/traderFees", payload=mock_fees_response)

            async with CoinmateAPI("test_key", "test_secret", "test_client") as api:
                result = await api.get_trading_fees("BTC_EUR")

            assert result is None

    async def test_get_trading_fees_no_credentials(self):
        """Test trading fees retrieval without credentials"""
        async with CoinmateAPI() as api:
            result = await api.get_trading_fees("BTC_EUR")

        assert result is None


@pytest.mark.unit
class TestCoinmateUtilityFunctions:

    async def test_get_coinmate_btc_czk_price_success(
        self, mock_coinmate_ticker_response
    ):
        """Test utility function for getting BTC/CZK price"""
        with aioresponses() as m:
            m.get(
                "https://coinmate.io/api/ticker?currencyPair=BTC_CZK",
                payload=mock_coinmate_ticker_response,
            )

            price = await get_coinmate_btc_czk_price()

            assert price == 2450000.0

    async def test_get_coinmate_btc_czk_price_error(self, mock_coinmate_error_response):
        """Test utility function with API error"""
        with aioresponses() as m:
            m.get(
                "https://coinmate.io/api/ticker?currencyPair=BTC_CZK",
                payload=mock_coinmate_error_response,
            )

            price = await get_coinmate_btc_czk_price()

            assert price is None

    async def test_get_coinmate_btc_czk_price_network_error(self):
        """Test utility function with network error"""
        with aioresponses() as m:
            m.get(
                "https://coinmate.io/api/ticker?currencyPair=BTC_CZK",
                exception=Exception("Network error"),
            )

            price = await get_coinmate_btc_czk_price()

            assert price is None


