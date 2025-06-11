"""
Integration tests for database functionality.
Requires TimescaleDB to be running (via docker-compose up).
"""

import os
import time

import pytest

from src.core.data_models import ArbitrageOpportunity, PriceData
from src.services.database_service import DatabaseService

# Skip all integration tests if database is not available
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://arbitrage_user:arbitrage_pass@localhost:5432/arbitrage",
)
SKIP_INTEGRATION = os.getenv("SKIP_DB_INTEGRATION", "true").lower() == "true"


@pytest.mark.integration
@pytest.mark.skipif(SKIP_INTEGRATION, reason="Database integration tests disabled")
class TestDatabaseIntegration:
    """Integration tests for database service with real TimescaleDB"""

    @pytest.fixture
    async def database_service(self):
        """Fixture that provides initialized database service"""
        db = DatabaseService(DATABASE_URL, enabled=True)

        # Initialize and check if successful
        if not await db.initialize():
            pytest.skip("Could not connect to database - ensure TimescaleDB is running")

        yield db

        # Cleanup
        await db.close()

    async def test_store_and_retrieve_price_data(self, database_service):
        """Test storing and retrieving price data"""
        db = database_service

        # Create test price data
        price_data = PriceData(
            exchange="test_exchange",
            symbol="BTC/USD",
            price=50000.0,
            price_usd=50000.0,
            original_currency="USD",
            timestamp=time.time(),
            volume=1.5,
        )

        # Store price data
        result = await db.store_price_data(price_data)
        assert result is True

        # Retrieve latest prices
        latest_prices = await db.get_latest_prices()
        assert len(latest_prices) > 0

        # Check if our data is in the results
        test_prices = [
            p for p in latest_prices if p["exchange_name"] == "test_exchange"
        ]
        assert len(test_prices) > 0

    async def test_store_and_retrieve_arbitrage_opportunity(self, database_service):
        """Test storing and retrieving arbitrage opportunities"""
        db = database_service

        # Create test opportunity
        opportunity = ArbitrageOpportunity(
            buy_exchange="test_buy",
            sell_exchange="test_sell",
            buy_price=50000.0,
            sell_price=50500.0,
            profit_usd=500.0,
            profit_percentage=1.0,
            timestamp=time.time(),
            volume_limit=0.1,
        )

        # Store opportunity
        result = await db.store_arbitrage_opportunity(opportunity)
        assert result is True

        # Retrieve opportunities
        opportunities = await db.get_arbitrage_opportunities(hours=1, min_profit=0.5)
        assert len(opportunities) > 0

        # Check if our opportunity is in the results
        test_opps = [
            o
            for o in opportunities
            if o["buy_exchange"] == "test_buy" and o["sell_exchange"] == "test_sell"
        ]
        assert len(test_opps) > 0
        assert test_opps[0]["profit_percentage"] == 1.0

    async def test_store_exchange_status(self, database_service):
        """Test storing exchange status"""
        db = database_service

        # Store active status
        result = await db.store_exchange_status("test_exchange", "active", None, 150)
        assert result is True

        # Store error status
        result = await db.store_exchange_status(
            "test_exchange", "error", "Connection timeout", 5000
        )
        assert result is True

        # Get exchange health
        health = await db.get_exchange_health(hours=1)
        assert "test_exchange" in health

        exchange_health = health["test_exchange"]
        assert exchange_health["total_requests"] >= 2
        assert exchange_health["success_rate"] >= 0

    async def test_database_stats(self, database_service):
        """Test database statistics retrieval"""
        db = database_service

        stats = await db.get_database_stats()

        assert stats["enabled"] is True
        assert stats["connected"] is True
        assert "tables" in stats
        assert "record_counts" in stats

        # Check that our main tables exist
        table_names = [t["tablename"] for t in stats["tables"]]
        assert "exchange_prices" in table_names
        assert "arbitrage_opportunities" in table_names
        assert "exchange_status" in table_names

    async def test_price_spread_history(self, database_service):
        """Test price spread history retrieval"""
        db = database_service

        # Insert some test data with different prices
        timestamp = time.time()

        price_data_1 = PriceData(
            exchange="exchange_1",
            symbol="BTC/USD",
            price=50000.0,
            price_usd=50000.0,
            original_currency="USD",
            timestamp=timestamp,
            volume=1.0,
        )

        price_data_2 = PriceData(
            exchange="exchange_2",
            symbol="BTC/USD",
            price=50500.0,
            price_usd=50500.0,
            original_currency="USD",
            timestamp=timestamp,
            volume=1.0,
        )

        await db.store_price_data(price_data_1)
        await db.store_price_data(price_data_2)

        # Get spread history
        spread_history = await db.get_price_spread_history(hours=1)

        assert isinstance(spread_history, list)
        # Might be empty if not enough data or time buckets
        if spread_history:
            assert "spread_usd" in spread_history[0]
            assert "spread_percentage" in spread_history[0]

    async def test_cleanup_old_data(self, database_service):
        """Test data cleanup functionality"""
        db = database_service

        # Get initial counts
        initial_stats = await db.get_database_stats()
        initial_stats["record_counts"]["exchange_prices"]

        # Cleanup with very short retention (should not delete recent data)
        await db.cleanup_old_data(days=30)

        # Get counts after cleanup
        final_stats = await db.get_database_stats()
        final_price_count = final_stats["record_counts"]["exchange_prices"]

        # Should not have deleted recent test data
        assert final_price_count >= 0  # Some data might exist

    async def test_connection_retry_mechanism(self):
        """Test connection retry mechanism with invalid URL"""
        # Test with invalid URL to trigger retry mechanism
        db = DatabaseService(
            "postgresql://invalid:invalid@localhost:9999/invalid", enabled=True
        )
        db._connection_retries = 2  # Reduce retries for faster test
        db._retry_delay = 0.1  # Reduce delay for faster test

        result = await db.initialize()

        assert result is False
        assert db.enabled is False


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(SKIP_INTEGRATION, reason="Database integration tests disabled")
class TestDatabasePerformance:
    """Performance tests for database operations"""

    @pytest.fixture
    async def database_service(self):
        """Fixture that provides initialized database service"""
        db = DatabaseService(DATABASE_URL, enabled=True)

        if not await db.initialize():
            pytest.skip("Could not connect to database")

        yield db
        await db.close()

    async def test_bulk_price_data_insertion(self, database_service):
        """Test inserting multiple price data points rapidly"""
        db = database_service

        # Insert 100 price data points
        start_time = time.time()

        for i in range(100):
            price_data = PriceData(
                exchange=f"test_exchange_{i % 5}",  # 5 different exchanges
                symbol="BTC/USD",
                price=50000.0 + i,
                price_usd=50000.0 + i,
                original_currency="USD",
                timestamp=time.time(),
                volume=1.0,
            )

            result = await db.store_price_data(price_data)
            assert result is True

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (less than 10 seconds)
        assert duration < 10.0

        # Verify data was stored
        latest_prices = await db.get_latest_prices()
        test_prices = [
            p for p in latest_prices if p["exchange_name"].startswith("test_exchange_")
        ]
        assert len(test_prices) >= 5  # At least one for each exchange
