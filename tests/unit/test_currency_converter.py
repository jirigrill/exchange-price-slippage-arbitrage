"""
Tests for the currency converter module.
"""

import pytest
from unittest.mock import patch, AsyncMock
from src.services.currency_converter import CurrencyConverter


@pytest.mark.unit
class TestCurrencyConverter:

    async def test_same_currency_conversion(self):
        """Test conversion when from and to currencies are the same"""
        converter = CurrencyConverter()
        rate = await converter.get_exchange_rate("USD", "USD")
        assert rate == 1.0

    async def test_usdt_usd_conversion(self):
        """Test USDT to USD conversion (should be 1:1)"""
        converter = CurrencyConverter()

        # USDT to USD
        rate = await converter.get_exchange_rate("USDT", "USD")
        assert rate == 1.0

        # USD to USDT
        rate = await converter.get_exchange_rate("USD", "USDT")
        assert rate == 1.0

    async def test_convert_to_usd_same_currency(self):
        """Test USD conversion when already in USD or USDT"""
        converter = CurrencyConverter()

        # USD
        result = await converter.convert_to_usd(100.0, "USD")
        assert result == 100.0

        # USDT (treated as USD)
        result = await converter.convert_to_usd(100.0, "USDT")
        assert result == 100.0

    @patch("src.services.currency_converter.CurrencyConverter._update_exchange_rates")
    async def test_get_exchange_rate_with_cache(self, mock_update):
        """Test exchange rate retrieval with caching"""
        converter = CurrencyConverter()
        converter.exchange_rates = {"CZK/USD": 0.0417}
        converter.last_update = 1703254800.0

        # Mock time to avoid cache expiration
        with patch("time.time", return_value=1703254900.0):  # 100 seconds later
            rate = await converter.get_exchange_rate("CZK", "USD")
            assert rate == 0.0417

        # Should not update since cache is fresh
        mock_update.assert_not_called()

    @patch("aiohttp.ClientSession.get")
    async def test_update_exchange_rates_success(self, mock_get):
        """Test successful exchange rate update from API"""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "rates": {"CZK": 24.0, "EUR": 0.85, "GBP": 0.75}
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        converter = CurrencyConverter()
        await converter._update_exchange_rates()

        # Check if rates were stored correctly
        assert converter.exchange_rates["USD/CZK"] == 24.0
        assert converter.exchange_rates["CZK/USD"] == 1.0 / 24.0
        assert converter.last_update > 0

    @patch("aiohttp.ClientSession.get")
    async def test_update_exchange_rates_failure(self, mock_get):
        """Test exchange rate update failure handling"""
        # Mock failed API response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response

        converter = CurrencyConverter()
        old_last_update = converter.last_update

        await converter._update_exchange_rates()

        # Should not update timestamp on failure
        assert converter.last_update == old_last_update

    async def test_convert_to_usd_with_rate(self, mock_currency_converter):
        """Test USD conversion with exchange rate"""
        # Ensure we don't update rates during test by setting recent timestamp
        import time

        mock_currency_converter.last_update = time.time()

        result = await mock_currency_converter.convert_to_usd(2400000.0, "CZK")

        # 2400000 CZK * 0.0417 USD/CZK = 100080 USD
        expected = 2400000.0 * 0.0417
        assert result == pytest.approx(
            expected, rel=1e-3
        )  # Allow small relative tolerance

    async def test_convert_to_usd_unknown_currency(self, mock_currency_converter):
        """Test USD conversion with unknown currency"""
        result = await mock_currency_converter.convert_to_usd(100.0, "XYZ")
        assert result is None


@pytest.mark.integration
class TestCurrencyConverterIntegration:

    @pytest.mark.slow
    async def test_real_api_call(self):
        """Test actual API call (marked as slow)"""
        converter = CurrencyConverter()

        # This will make a real API call
        rate = await converter.get_exchange_rate("EUR", "USD")

        # Basic sanity checks
        assert rate is not None
        assert rate > 0
        assert 0.5 < rate < 2.0  # EUR/USD should be in reasonable range
