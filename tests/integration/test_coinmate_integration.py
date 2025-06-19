"""
Integration tests for Coinmate API - tests real API connectivity
These tests verify that the API endpoints are reachable and return expected response structure.
They do not assert specific values, only that the service is properly connected.
"""

import pytest

from src.apis.coinmate.api import CoinmateAPI


@pytest.mark.integration
class TestCoinmateAPIIntegration:
    """Integration tests for Coinmate API real connectivity"""

    @pytest.mark.slow
    async def test_ticker_endpoint_connectivity(self):
        """Test that ticker endpoint is accessible and returns valid structure"""
        async with CoinmateAPI() as api:
            result = await api.get_ticker("BTC_CZK")

        # Verify we got a response (not None)
        assert result is not None
        
        # Verify response has expected structure
        assert "error" in result
        
        # If successful, verify data structure
        if not result.get("error", True):
            assert "data" in result
            data = result["data"]
            assert "last" in data
            assert "bid" in data
            assert "ask" in data
            assert "amount" in data

    @pytest.mark.slow
    async def test_orderbook_endpoint_connectivity(self):
        """Test that orderbook endpoint is accessible and returns valid structure"""
        async with CoinmateAPI() as api:
            result = await api.get_orderbook("BTC_CZK")

        # Verify we got a response (not None)
        assert result is not None
        
        # Verify response has expected structure
        assert "error" in result
        
        # If successful, verify data structure
        if not result.get("error", True):
            assert "data" in result
            data = result["data"]
            assert "asks" in data
            assert "bids" in data
            assert isinstance(data["asks"], list)
            assert isinstance(data["bids"], list)

    @pytest.mark.slow
    async def test_trading_pairs_endpoint_connectivity(self):
        """Test that trading pairs endpoint is accessible and returns valid structure"""
        async with CoinmateAPI() as api:
            result = await api.get_trading_pairs()

        # Verify we got a response (not None)
        assert result is not None
        
        # Verify response has expected structure
        assert "error" in result
        
        # If successful, verify data structure
        if not result.get("error", True):
            assert "data" in result
            data = result["data"]
            assert isinstance(data, list)
            assert len(data) > 0  # Should have at least some trading pairs

    @pytest.mark.slow
    async def test_transactions_endpoint_connectivity(self):
        """Test that transactions endpoint is accessible and returns valid structure"""
        async with CoinmateAPI() as api:
            result = await api.get_transactions("BTC_CZK", 60)

        # Verify we got a response (not None)
        assert result is not None
        
        # Verify response has expected structure
        assert "error" in result
        
        # If successful, verify data structure
        if not result.get("error", True):
            assert "data" in result
            data = result["data"]
            assert isinstance(data, list)

    @pytest.mark.slow 
    async def test_authenticated_endpoint_structure(self):
        """Test that authenticated endpoints raise proper error when no credentials"""
        async with CoinmateAPI() as api:
            with pytest.raises(ValueError, match="API credentials required"):
                await api.get_balance()

    @pytest.mark.slow
    async def test_trading_fees_endpoint_structure(self):
        """Test that trading fees endpoint returns None when no credentials"""
        async with CoinmateAPI() as api:
            result = await api.get_trading_fees("BTC_CZK")

        # Should return None when no credentials (handled gracefully in this method)
        assert result is None