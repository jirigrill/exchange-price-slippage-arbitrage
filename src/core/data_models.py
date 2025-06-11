"""
Data models for exchange monitoring and arbitrage detection.
"""

from dataclasses import dataclass


@dataclass
class PriceData:
    exchange: str
    symbol: str
    price: float
    price_usd: float  # Price converted to USD
    original_currency: str  # Original quote currency
    timestamp: float
    volume: float = 0.0


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
