"""
Database service for storing exchange price data and arbitrage opportunities in TimescaleDB.

This service handles all database operations including:
- Storing price data from exchanges
- Recording arbitrage opportunities
- Tracking exchange health status
- Providing analytics queries
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import asyncpg

from config.settings import TIMEZONE
from ..core.data_models import ArbitrageOpportunity, PriceData
from ..utils.logging import log_with_timestamp


class DatabaseService:
    """Service for interacting with TimescaleDB to store arbitrage monitoring data."""

    def __init__(self, database_url: str, enabled: bool = True):
        """
        Initialize database service.

        Args:
            database_url: PostgreSQL connection URL
            enabled: Whether database operations are enabled
        """
        self.database_url = database_url
        self.enabled = enabled
        self.pool: Optional[asyncpg.Pool] = None
        self._connection_retries = 3
        self._retry_delay = 5
        self.timezone = TIMEZONE

    async def initialize(self) -> bool:
        """
        Initialize database connection pool.

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            log_with_timestamp("📊 Database: disabled via configuration")
            return True

        try:
            log_with_timestamp("📊 Database: initializing connection pool...")

            # Retry connection with exponential backoff
            for attempt in range(self._connection_retries):
                try:
                    self.pool = await asyncpg.create_pool(
                        self.database_url,
                        min_size=2,
                        max_size=10,
                        command_timeout=30,
                        server_settings={
                            "application_name": "arbitrage_monitor",
                            "timezone": "UTC",
                        },
                    )

                    # Test connection
                    async with self.pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")

                    log_with_timestamp(
                        "✓ Database: connection pool initialized successfully"
                    )
                    return True

                except Exception as e:
                    if attempt < self._connection_retries - 1:
                        log_with_timestamp(
                            f"⚠ Database: connection attempt {attempt + 1} failed: {e}, "
                            f"retrying in {self._retry_delay}s..."
                        )
                        await asyncio.sleep(self._retry_delay * (attempt + 1))
                    else:
                        raise

        except Exception as e:
            log_with_timestamp(f"✗ Database: failed to initialize: {e}")
            self.enabled = False
            return False

    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            log_with_timestamp("📊 Database: connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool."""
        if not self.enabled or not self.pool:
            yield None
            return

        async with self.pool.acquire() as conn:
            yield conn

    def _get_timezone_expression(self, timestamp_column: str) -> str:
        """Get timezone-aware timestamp expression for SQL queries."""
        if self.timezone and self.timezone.upper() != "UTC":
            return f"{timestamp_column} AT TIME ZONE '{self.timezone}'"
        return timestamp_column

    async def store_price_data(self, price_data: PriceData) -> bool:
        """
        Store exchange price data in TimescaleDB.

        Args:
            price_data: Price data from exchange monitor

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return True

        try:
            async with self.get_connection() as conn:
                if conn is None:
                    return False

                await conn.execute(
                    """
                    INSERT INTO exchange_prices
                    (exchange_name, symbol, price, price_usd, original_currency, volume, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, to_timestamp($7) AT TIME ZONE 'UTC')
                    """,
                    price_data.exchange,
                    price_data.symbol,
                    float(price_data.price),
                    float(price_data.price_usd),
                    price_data.original_currency,
                    float(price_data.volume),
                    price_data.timestamp,
                )

            return True

        except Exception as e:
            log_with_timestamp(f"✗ Database: failed to store price data: {e}")
            return False

    async def store_arbitrage_opportunity(
        self, opportunity: ArbitrageOpportunity
    ) -> bool:
        """
        Store arbitrage opportunity in TimescaleDB.

        Args:
            opportunity: Detected arbitrage opportunity

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return True

        try:
            async with self.get_connection() as conn:
                if conn is None:
                    return False

                await conn.execute(
                    """
                    INSERT INTO arbitrage_opportunities
                    (buy_exchange, sell_exchange, buy_price, sell_price, profit_usd,
                     profit_percentage, volume_limit, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, to_timestamp($8) AT TIME ZONE 'UTC')
                    """,
                    opportunity.buy_exchange,
                    opportunity.sell_exchange,
                    float(opportunity.buy_price),
                    float(opportunity.sell_price),
                    float(opportunity.profit_usd),
                    float(opportunity.profit_percentage),
                    float(opportunity.volume_limit),
                    opportunity.timestamp,
                )

            return True

        except Exception as e:
            log_with_timestamp(
                f"✗ Database: failed to store arbitrage opportunity: {e}"
            )
            return False

    async def store_exchange_status(
        self,
        exchange_name: str,
        status: str,
        error_message: Optional[str] = None,
        response_time_ms: Optional[int] = None,
    ) -> bool:
        """
        Store exchange health status.

        Args:
            exchange_name: Name of the exchange
            status: Status ('active', 'error', 'timeout')
            error_message: Error message if applicable
            response_time_ms: Response time in milliseconds

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return True

        try:
            async with self.get_connection() as conn:
                if conn is None:
                    return False

                await conn.execute(
                    """
                    INSERT INTO exchange_status
                    (exchange_name, status, error_message, response_time_ms)
                    VALUES ($1, $2, $3, $4)
                    """,
                    exchange_name,
                    status,
                    error_message,
                    response_time_ms,
                )

            return True

        except Exception as e:
            log_with_timestamp(f"✗ Database: failed to store exchange status: {e}")
            return False

    async def get_latest_prices(self) -> List[Dict]:
        """
        Get latest prices for all exchanges.

        Returns:
            List of price records
        """
        if not self.enabled:
            return []

        try:
            async with self.get_connection() as conn:
                if conn is None:
                    return []

                # Use timezone-aware query for better user experience
                timezone_expr = self._get_timezone_expression("timestamp")
                query = f"""
                    SELECT DISTINCT ON (exchange_name, symbol)
                        exchange_name,
                        symbol,
                        price_usd,
                        {timezone_expr} as timestamp
                    FROM exchange_prices
                    ORDER BY exchange_name, symbol, timestamp DESC
                """
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]

        except Exception as e:
            log_with_timestamp(f"✗ Database: failed to get latest prices: {e}")
            return []

    async def get_price_spread_history(self, hours: int = 24) -> List[Dict]:
        """
        Get price spread history for specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            List of spread records
        """
        if not self.enabled:
            return []

        try:
            async with self.get_connection() as conn:
                if conn is None:
                    return []

                # Use timezone-aware query
                timezone_expr = self._get_timezone_expression(
                    "time_bucket('1 hour', ep.timestamp)"
                )
                query = f"""
                    SELECT
                        {timezone_expr} as bucket,
                        MIN(ep.price_usd) as min_price,
                        MAX(ep.price_usd) as max_price,
                        (MAX(ep.price_usd) - MIN(ep.price_usd)) as spread_usd,
                        CASE
                            WHEN MIN(ep.price_usd) > 0 THEN
                                ((MAX(ep.price_usd) - MIN(ep.price_usd)) / MIN(ep.price_usd)) * 100
                            ELSE 0
                        END as spread_percentage
                    FROM exchange_prices ep
                    WHERE ep.timestamp >= NOW() - ($1 || ' hours')::INTERVAL
                        AND ep.symbol LIKE '%BTC%'
                    GROUP BY time_bucket('1 hour', ep.timestamp)
                    ORDER BY bucket DESC
                """
                rows = await conn.fetch(query, hours)
                return [dict(row) for row in rows]

        except Exception as e:
            log_with_timestamp(f"✗ Database: failed to get spread history: {e}")
            return []

    async def get_arbitrage_opportunities(
        self, hours: int = 24, min_profit: float = 0.1
    ) -> List[Dict]:
        """
        Get arbitrage opportunities from specified time period.

        Args:
            hours: Number of hours to look back
            min_profit: Minimum profit percentage threshold

        Returns:
            List of arbitrage opportunity records
        """
        if not self.enabled:
            return []

        try:
            async with self.get_connection() as conn:
                if conn is None:
                    return []

                timezone_expr = self._get_timezone_expression("timestamp")
                query = f"""
                    SELECT
                        buy_exchange,
                        sell_exchange,
                        buy_price,
                        sell_price,
                        profit_usd,
                        profit_percentage,
                        volume_limit,
                        {timezone_expr} as timestamp
                    FROM arbitrage_opportunities
                    WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                        AND profit_percentage >= $1
                    ORDER BY timestamp DESC, profit_percentage DESC
                    LIMIT 100
                """
                rows = await conn.fetch(query, min_profit)
                return [dict(row) for row in rows]

        except Exception as e:
            log_with_timestamp(
                f"✗ Database: failed to get arbitrage opportunities: {e}"
            )
            return []

    async def get_exchange_health(self, hours: int = 1) -> Dict[str, Dict]:
        """
        Get exchange health statistics for specified time period.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary mapping exchange names to health stats
        """
        if not self.enabled:
            return {}

        try:
            async with self.get_connection() as conn:
                if conn is None:
                    return {}

                rows = await conn.fetch(
                    """
                    SELECT
                        exchange_name,
                        COUNT(*) as total_requests,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as successful_requests,
                        AVG(response_time_ms) as avg_response_time,
                        MAX(timestamp) as last_seen
                    FROM exchange_status
                    WHERE timestamp >= NOW() - INTERVAL '%s hours'
                    GROUP BY exchange_name
                    """
                    % hours
                )

                result = {}
                for row in rows:
                    exchange_name = row["exchange_name"]
                    total_req = row["total_requests"]
                    success_req = row["successful_requests"]
                    avg_time = row["avg_response_time"]

                    result[exchange_name] = {
                        "total_requests": total_req,
                        "successful_requests": success_req,
                        "success_rate": (
                            (success_req / total_req) * 100 if total_req > 0 else 0
                        ),
                        "avg_response_time": (
                            float(avg_time) if avg_time else None
                        ),
                        "last_seen": row["last_seen"],
                    }

                return result

        except Exception as e:
            log_with_timestamp(f"✗ Database: failed to get exchange health: {e}")
            return {}

    async def cleanup_old_data(self, days: int = 30):
        """
        Clean up old data beyond retention period.

        Args:
            days: Number of days to retain data
        """
        if not self.enabled:
            return

        try:
            async with self.get_connection() as conn:
                if conn is None:
                    return

                # Clean up old price data
                price_query = (
                    "DELETE FROM exchange_prices "
                    "WHERE timestamp < NOW() - INTERVAL '%s days' "
                    "RETURNING COUNT(*)"
                ) % days
                deleted_prices = await conn.fetchval(price_query)

                # Clean up old arbitrage opportunities
                opp_query = (
                    "DELETE FROM arbitrage_opportunities "
                    "WHERE timestamp < NOW() - INTERVAL '%s days' "
                    "RETURNING COUNT(*)"
                ) % days
                deleted_opportunities = await conn.fetchval(opp_query)

                # Clean up old exchange status (keep for shorter period)
                status_query = (
                    "DELETE FROM exchange_status "
                    "WHERE timestamp < NOW() - INTERVAL '%s days' "
                    "RETURNING COUNT(*)"
                ) % min(days, 7)
                deleted_status = await conn.fetchval(status_query)

                if any([deleted_prices, deleted_opportunities, deleted_status]):
                    log_with_timestamp(
                        f"📊 Database: cleaned up old data - "
                        f"prices: {deleted_prices or 0}, "
                        f"opportunities: {deleted_opportunities or 0}, "
                        f"status: {deleted_status or 0}"
                    )

        except Exception as e:
            log_with_timestamp(f"✗ Database: failed to cleanup old data: {e}")

    async def get_database_stats(self) -> Dict:
        """
        Get database statistics and health information.

        Returns:
            Dictionary with database statistics
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            async with self.get_connection() as conn:
                if conn is None:
                    return {"enabled": True, "connected": False}

                # Get table sizes and record counts
                stats_query = """
                    SELECT
                        schemaname,
                        relname as tablename,
                        pg_size_pretty(
                            pg_total_relation_size(schemaname||'.'||relname)
                        ) as size,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(
                        schemaname||'.'||relname
                    ) DESC
                """
                stats = await conn.fetch(stats_query)

                # Get record counts
                price_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM exchange_prices"
                )
                opportunity_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM arbitrage_opportunities"
                )
                status_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM exchange_status"
                )

                return {
                    "enabled": True,
                    "connected": True,
                    "tables": [dict(row) for row in stats],
                    "record_counts": {
                        "exchange_prices": price_count,
                        "arbitrage_opportunities": opportunity_count,
                        "exchange_status": status_count,
                    },
                }

        except Exception as e:
            log_with_timestamp(f"✗ Database: failed to get stats: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}
