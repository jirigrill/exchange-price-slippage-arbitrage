import time
from dataclasses import dataclass
from typing import List, Optional

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
        self.large_exchanges = ["kraken"]
        self.small_exchanges = ["coinmate"]

    def detect_opportunities(self) -> List[ArbitrageOpportunity]:
        current_opportunities = []

        spread_data = self.monitor.get_price_spread()
        if not spread_data:
            return current_opportunities

        latest_prices = self.monitor.latest_prices

        for buy_exchange, buy_data in latest_prices.items():
            for sell_exchange, sell_data in latest_prices.items():
                if buy_exchange == sell_exchange:
                    continue

                if self._is_valid_arbitrage_pair(buy_exchange, sell_exchange):
                    opportunity = self._calculate_opportunity(
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

        trading_fees = self._estimate_trading_fees(buy_exchange, sell_exchange)
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

    def _estimate_trading_fees(self, buy_exchange: str, sell_exchange: str) -> float:
        fee_estimates = {"kraken": 0.26, "coinmate": 0.35}

        buy_fee = fee_estimates.get(buy_exchange, 0.25)
        sell_fee = fee_estimates.get(sell_exchange, 0.25)

        return buy_fee + sell_fee

    def get_best_opportunities(self, limit: int = 5) -> List[ArbitrageOpportunity]:
        recent_opportunities = [
            opp for opp in self.opportunities if time.time() - opp.timestamp < 300
        ]

        recent_opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        return recent_opportunities[:limit]
