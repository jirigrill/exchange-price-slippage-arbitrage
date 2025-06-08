import time
from dataclasses import dataclass
from typing import List, Optional

from config.settings import (
    COINMATE_TRADING_FEE,
    DEFAULT_TRADING_FEE,
    DYNAMIC_FEES_ENABLED,
    KRAKEN_TRADING_FEE,
    LARGE_EXCHANGES,
    SMALL_EXCHANGES,
)

from ..apis.coinmate_api import CoinmateAPI
from ..apis.kraken_api import KrakenAPI
from ..utils.logging import log_with_timestamp
from .exchange_monitor import ExchangeMonitor, PriceData


@dataclass
class ArbitrageOpportunity:
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    profit_usd: float
    profit_percentage: float
    timestamp: float
    volume_limit: float


class ArbitrageDetector:
    def __init__(self, monitor: ExchangeMonitor, min_profit_percentage: float = 0.1):
        self.monitor = monitor
        self.min_profit_percentage = min_profit_percentage
        self.opportunities = []
        self.large_exchanges = LARGE_EXCHANGES
        self.small_exchanges = SMALL_EXCHANGES
        self._fee_cache = {}  # Cache for dynamic fees
        self._fee_cache_timestamp = {}  # Cache timestamps

    async def detect_opportunities(self) -> List[ArbitrageOpportunity]:
        """
        Detect arbitrage opportunities from current prices
        Returns a list of profitable opportunities
        """
        if not self.monitor.latest_prices:
            return []

        current_opportunities = []
        exchanges = list(self.monitor.latest_prices.keys())

        # Check all valid exchange pairs
        for i, buy_exchange in enumerate(exchanges):
            for j, sell_exchange in enumerate(exchanges):
                if i != j and self._is_valid_arbitrage_pair(
                    buy_exchange, sell_exchange
                ):
                    buy_data = self.monitor.latest_prices[buy_exchange]
                    sell_data = self.monitor.latest_prices[sell_exchange]

                    opportunity = await self._calculate_opportunity_async(
                        buy_exchange, buy_data, sell_exchange, sell_data
                    )
                    if (
                        opportunity
                        and opportunity.profit_percentage >= self.min_profit_percentage
                    ):
                        current_opportunities.append(opportunity)

        current_opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        self.opportunities.extend(current_opportunities)

        return current_opportunities

    def _is_valid_arbitrage_pair(self, buy_exchange: str, sell_exchange: str) -> bool:
        return (
            buy_exchange in self.large_exchanges
            and sell_exchange in self.small_exchanges
        ) or (
            buy_exchange in self.small_exchanges
            and sell_exchange in self.large_exchanges
        )

    def _calculate_opportunity(
        self,
        buy_exchange: str,
        buy_data: PriceData,
        sell_exchange: str,
        sell_data: PriceData,
    ) -> Optional[ArbitrageOpportunity]:

        # Use USD prices for comparison
        if sell_data.price_usd <= buy_data.price_usd:
            return None

        profit_usd = sell_data.price_usd - buy_data.price_usd
        profit_percentage = (profit_usd / buy_data.price_usd) * 100

        # Note: This will be updated to async in detect_opportunities method
        trading_fees = 0  # Placeholder, calculated in async context
        net_profit_percentage = profit_percentage - trading_fees

        if net_profit_percentage <= 0:
            return None

        volume_limit = min(buy_data.volume, sell_data.volume) * 0.1

        return ArbitrageOpportunity(
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            buy_price=buy_data.price_usd,
            sell_price=sell_data.price_usd,
            profit_usd=profit_usd,
            profit_percentage=net_profit_percentage,
            timestamp=time.time(),
            volume_limit=volume_limit,
        )

    async def _calculate_opportunity_async(
        self,
        buy_exchange: str,
        buy_data,
        sell_exchange: str,
        sell_data,
    ) -> Optional[ArbitrageOpportunity]:
        """Async version of opportunity calculation with dynamic fees"""
        # Use USD prices for comparison
        if sell_data.price_usd <= buy_data.price_usd:
            return None

        profit_usd = sell_data.price_usd - buy_data.price_usd
        profit_percentage = (profit_usd / buy_data.price_usd) * 100

        trading_fees = await self._get_trading_fees(buy_exchange, sell_exchange)
        net_profit_percentage = profit_percentage - trading_fees

        if net_profit_percentage <= 0:
            return None

        volume_limit = min(buy_data.volume, sell_data.volume) * 0.1

        # Log fee information for transparency
        log_with_timestamp(
            f"💰 Fee calculation: {buy_exchange}+{sell_exchange} = {trading_fees:.2f}% "
            f"(gross: {profit_percentage:.2f}% → net: {net_profit_percentage:.2f}%)"
        )

        return ArbitrageOpportunity(
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            buy_price=buy_data.price_usd,
            sell_price=sell_data.price_usd,
            profit_usd=profit_usd,
            profit_percentage=net_profit_percentage,
            timestamp=time.time(),
            volume_limit=volume_limit,
        )

    async def _get_trading_fees(self, buy_exchange: str, sell_exchange: str) -> float:
        """Get trading fees, either from cache, API, or config"""
        buy_fee = await self._get_exchange_fee(buy_exchange)
        sell_fee = await self._get_exchange_fee(sell_exchange)
        return buy_fee + sell_fee

    async def _get_exchange_fee(self, exchange: str) -> float:
        """Get fee for a specific exchange"""
        if DYNAMIC_FEES_ENABLED:
            # Try to get from cache first (cache for 1 hour)
            cache_key = f"{exchange}_fee"
            cache_time = self._fee_cache_timestamp.get(cache_key, 0)
            if time.time() - cache_time < 3600 and cache_key in self._fee_cache:
                return self._fee_cache[cache_key]

            # Fetch from API
            dynamic_fee = await self._fetch_dynamic_fee(exchange)
            if dynamic_fee is not None:
                self._fee_cache[cache_key] = dynamic_fee
                self._fee_cache_timestamp[cache_key] = time.time()
                log_with_timestamp(
                    f"📊 Dynamic fee: {exchange} = {dynamic_fee:.2f}% (fetched from API, cached for 1h)"
                )
                return dynamic_fee

        # Fallback to configured static fees
        static_fees = {
            "kraken": KRAKEN_TRADING_FEE,
            "coinmate": COINMATE_TRADING_FEE,
        }
        fallback_fee = static_fees.get(exchange, DEFAULT_TRADING_FEE)
        log_with_timestamp(f"📊 Static fee: {exchange} = {fallback_fee:.2f}% (using configured value)")
        return fallback_fee

    async def _fetch_dynamic_fee(self, exchange: str) -> Optional[float]:
        """Fetch current trading fee from exchange API"""
        try:
            if exchange == "kraken":
                # Get Kraken credentials from monitor
                kraken_creds = self.monitor.api_keys.get("kraken", {})
                api_key = kraken_creds.get("apiKey")
                api_secret = kraken_creds.get("secret")
                
                async with KrakenAPI(api_key, api_secret) as api:
                    return await api.get_trading_fees("BTCUSD")
                    
            elif exchange == "coinmate":
                # Get Coinmate credentials from monitor
                coinmate_creds = self.monitor.api_keys.get("coinmate", {})
                api_key = coinmate_creds.get("apiKey")
                api_secret = coinmate_creds.get("secret")
                client_id = coinmate_creds.get("clientId")
                
                async with CoinmateAPI(api_key, api_secret, client_id) as api:
                    return await api.get_trading_fees("BTC_CZK")
        except Exception as e:
            log_with_timestamp(f"⚠ Failed to fetch {exchange} fees: {e}")
        return None

    def get_best_opportunities(self, limit: int = 5) -> List[ArbitrageOpportunity]:
        recent_opportunities = [
            opp for opp in self.opportunities if time.time() - opp.timestamp < 300
        ]

        recent_opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        return recent_opportunities[:limit]
