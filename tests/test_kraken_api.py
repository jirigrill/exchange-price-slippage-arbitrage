"""
Tests for the Kraken API client.
"""

import pytest
from unittest.mock import patch, AsyncMock
from aioresponses import aioresponses
from src.kraken_api import KrakenAPI, get_kraken_btc_usd_price


@pytest.mark.unit
class TestKrakenAPI:

    async def test_init_without_credentials(self):
        """Test API initialization without credentials"""
        api = KrakenAPI()
        assert api.base_url == "https://api.kraken.com"
        assert api.api_key is None
        assert api.api_secret is None

    async def test_init_with_credentials(self):
        """Test API initialization with credentials"""
        api = KrakenAPI("test_key", "test_secret")
        assert api.api_key == "test_key"
        assert api.api_secret == "test_secret"

    async def test_get_ticker_success(self):
        """Test successful ticker retrieval"""
        mock_response = {
            "error": [],
            "result": {
                "BTCUSD": {
                    "a": ["102500.0", "1", "1.000"],
                    "b": ["102499.0", "2", "2.000"],
                    "c": ["102500.0", "0.15000000"],
                    "v": ["150.50000000", "200.75000000"],
                    "p": ["102450.0", "102475.0"],
                    "t": [100, 150],
                    "l": ["102400.0", "102350.0"],
                    "h": ["102600.0", "102650.0"],
                    "o": "102450.0",
                }
            },
        }

        with aioresponses() as m:
            m.get(
                "https://api.kraken.com/0/public/Ticker?pair=BTCUSD",
                payload=mock_response,
            )

            async with KrakenAPI() as api:
                result = await api.get_ticker("BTCUSD")

            assert result == mock_response
            assert result["error"] == []
            assert "BTCUSD" in result["result"]
            assert result["result"]["BTCUSD"]["c"][0] == "102500.0"

    async def test_get_ticker_error_response(self):
        """Test ticker retrieval with API error"""
        mock_error_response = {"error": ["EGeneral:Invalid arguments"]}

        with aioresponses() as m:
            m.get(
                "https://api.kraken.com/0/public/Ticker?pair=INVALID",
                payload=mock_error_response,
            )

            async with KrakenAPI() as api:
                result = await api.get_ticker("INVALID")

            assert result == mock_error_response
            assert result["error"] == ["EGeneral:Invalid arguments"]

    async def test_get_ticker_network_error(self):
        """Test ticker retrieval with network error"""
        with aioresponses() as m:
            m.get(
                "https://api.kraken.com/0/public/Ticker?pair=BTCUSD",
                exception=Exception("Network error"),
            )

            async with KrakenAPI() as api:
                result = await api.get_ticker("BTCUSD")

            assert result is None

    async def test_get_ticker_http_error(self):
        """Test ticker retrieval with HTTP error"""
        with aioresponses() as m:
            m.get("https://api.kraken.com/0/public/Ticker?pair=BTCUSD", status=500)

            async with KrakenAPI() as api:
                result = await api.get_ticker("BTCUSD")

            assert result is None

    async def test_get_ohlc_success(self):
        """Test successful OHLC retrieval"""
        mock_ohlc = {
            "error": [],
            "result": {
                "BTCUSD": [
                    [
                        1703254800,
                        "102400.0",
                        "102600.0",
                        "102350.0",
                        "102500.0",
                        "102475.0",
                        "150.5",
                        100,
                    ],
                    [
                        1703254860,
                        "102500.0",
                        "102650.0",
                        "102450.0",
                        "102550.0",
                        "102525.0",
                        "120.3",
                        85,
                    ],
                ],
                "last": 1703254860,
            },
        }

        with aioresponses() as m:
            m.get(
                "https://api.kraken.com/0/public/OHLC?pair=BTCUSD&interval=1",
                payload=mock_ohlc,
            )

            async with KrakenAPI() as api:
                result = await api.get_ohlc("BTCUSD", 1)

            assert result == mock_ohlc
            assert len(result["result"]["BTCUSD"]) == 2

    async def test_get_order_book_success(self):
        """Test successful order book retrieval"""
        mock_orderbook = {
            "error": [],
            "result": {
                "BTCUSD": {
                    "asks": [
                        ["102501.0", "0.5", 1703254800],
                        ["102502.0", "1.0", 1703254801],
                    ],
                    "bids": [
                        ["102499.0", "0.3", 1703254799],
                        ["102498.0", "0.8", 1703254798],
                    ],
                }
            },
        }

        with aioresponses() as m:
            m.get(
                "https://api.kraken.com/0/public/Depth?pair=BTCUSD&count=100",
                payload=mock_orderbook,
            )

            async with KrakenAPI() as api:
                result = await api.get_order_book("BTCUSD", 100)

            assert result == mock_orderbook
            assert len(result["result"]["BTCUSD"]["asks"]) == 2
            assert len(result["result"]["BTCUSD"]["bids"]) == 2

    async def test_get_asset_pairs_success(self):
        """Test successful asset pairs retrieval"""
        mock_pairs = {
            "error": [],
            "result": {
                "BTCUSD": {
                    "altname": "BTCUSD",
                    "wsname": "BTC/USD",
                    "aclass_base": "currency",
                    "base": "XXBT",
                    "aclass_quote": "currency",
                    "quote": "ZUSD",
                    "lot": "unit",
                    "pair_decimals": 1,
                    "lot_decimals": 8,
                }
            },
        }

        with aioresponses() as m:
            m.get("https://api.kraken.com/0/public/AssetPairs", payload=mock_pairs)

            async with KrakenAPI() as api:
                result = await api.get_asset_pairs()

            assert result == mock_pairs
            assert "BTCUSD" in result["result"]

    @patch("time.time", return_value=1703254800)
    @patch("src.kraken_api.KrakenAPI._generate_signature")
    async def test_authenticated_request(self, mock_signature, mock_time):
        """Test authenticated request creation"""
        mock_signature.return_value = "TEST_SIGNATURE"

        mock_balance = {
            "error": [],
            "result": {"XXBT": "1.5000000000", "ZUSD": "50000.0000"},
        }

        with aioresponses() as m:
            m.post("https://api.kraken.com/0/private/Balance", payload=mock_balance)

            async with KrakenAPI("test_key", "test_secret") as api:
                result = await api.get_account_balance()

            assert result == mock_balance
            mock_signature.assert_called_once()

    def test_generate_signature(self):
        """Test signature generation"""
        import base64

        # Create a valid base64-encoded secret
        test_secret_bytes = b"test_secret_key_for_hmac_generation"
        test_secret_b64 = base64.b64encode(test_secret_bytes).decode("utf-8")

        api = KrakenAPI("test_key", test_secret_b64)

        nonce = "1703254800000"
        data = {"pair": "BTCUSD"}

        signature = api._generate_signature("/0/public/Ticker", data, nonce)

        # Signature should be a base64 string
        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_generate_signature_no_secret(self):
        """Test signature generation without secret"""
        api = KrakenAPI("test_key", None)

        with pytest.raises(ValueError, match="API secret required"):
            api._generate_signature("/0/public/Ticker", {}, "123")


@pytest.mark.unit
class TestKrakenUtilityFunctions:

    async def test_get_kraken_btc_usd_price_success(self):
        """Test utility function for getting BTC/USD price"""
        mock_response = {
            "error": [],
            "result": {"BTCUSD": {"c": ["102500.0", "0.15000000"]}},
        }

        with aioresponses() as m:
            m.get(
                "https://api.kraken.com/0/public/Ticker?pair=BTCUSD",
                payload=mock_response,
            )

            price = await get_kraken_btc_usd_price()

            assert price == 102500.0

    async def test_get_kraken_btc_usd_price_xbt_format(self):
        """Test utility function with XBTUSD format"""
        mock_response = {
            "error": [],
            "result": {"XBTUSD": {"c": ["102500.0", "0.15000000"]}},
        }

        with aioresponses() as m:
            m.get(
                "https://api.kraken.com/0/public/Ticker?pair=BTCUSD",
                payload=mock_response,
            )

            price = await get_kraken_btc_usd_price()

            assert price == 102500.0

    async def test_get_kraken_btc_usd_price_error(self):
        """Test utility function with API error"""
        mock_error_response = {"error": ["EGeneral:Invalid arguments"]}

        with aioresponses() as m:
            m.get(
                "https://api.kraken.com/0/public/Ticker?pair=BTCUSD",
                payload=mock_error_response,
            )

            price = await get_kraken_btc_usd_price()

            assert price is None

    async def test_get_kraken_btc_usd_price_network_error(self):
        """Test utility function with network error"""
        with aioresponses() as m:
            m.get(
                "https://api.kraken.com/0/public/Ticker?pair=BTCUSD",
                exception=Exception("Network error"),
            )

            price = await get_kraken_btc_usd_price()

            assert price is None


@pytest.mark.integration
class TestKrakenAPIIntegration:

    @pytest.mark.slow
    async def test_real_ticker_call(self):
        """Test actual API call to Kraken (marked as slow)"""
        async with KrakenAPI() as api:
            result = await api.get_ticker("BTCUSD")

        # Basic sanity checks for real API response
        if result and not result.get("error"):
            result_data = result.get("result", {})
            # Should have either BTCUSD or XBTUSD
            btc_data = result_data.get("BTCUSD") or result_data.get("XBTUSD")

            if btc_data:
                last_price = btc_data.get("c", [None])[0]
                if last_price:
                    price = float(last_price)
                    # BTC price should be reasonable ($10K-$200K)
                    assert 10000 < price < 200000
                    assert "a" in btc_data  # Ask
                    assert "b" in btc_data  # Bid
                    assert "v" in btc_data  # Volume
