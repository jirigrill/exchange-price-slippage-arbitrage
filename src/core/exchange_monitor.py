import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..apis.base_exchange import BaseExchangeAPI, create_exchange_api
from ..services.currency_converter import CurrencyConverter
from ..utils.logging import log_with_timestamp


@dataclass
class PriceData:
    exchange: str
    symbol: str
    price: float
    price_usd: float  # Price converted to USD
    original_currency: str  # Original quote currency
    timestamp: float
    volume: float = 0.0


class ExchangeMonitor:
    def __init__(
        self,
        exchanges: List[str],
        trading_pairs: Dict[str, str],
        api_keys: Dict[str, Dict] = None,
        symbol: str = "BTC/USDT",
    ):
        self.exchanges = exchanges
        self.symbol = symbol
        self.trading_pairs = trading_pairs  # Exchange-specific trading pairs
        self.api_keys = api_keys or {}
        self.latest_prices = {}
        self.price_history = []
        self.currency_converter = CurrencyConverter()

        for exchange_name in exchanges:
            try:
                log_with_timestamp(f"✓ Initialized {exchange_name}")
            except Exception as e:
                log_with_timestamp(f"✗ Error initializing {exchange_name}: {e}")

    async def fetch_price(self, exchange_name: str) -> Optional[PriceData]:
        """Fetch price using the abstract exchange API interface"""
        # Get the trading pair for this exchange
        trading_pair = self.trading_pairs.get(exchange_name, self.symbol)

        try:
            # Get API credentials if available
            exchange_creds = self.api_keys.get(exchange_name, {})

            # Create exchange API using factory
            exchange_api = create_exchange_api(
                exchange_name,
                api_key=exchange_creds.get("apiKey"),
                api_secret=exchange_creds.get("secret"),
                client_id=exchange_creds.get("clientId"),  # Only used by Coinmate
            )

            price_data = await self._fetch_price_generic(exchange_api, trading_pair)

            if price_data:
                self.latest_prices[exchange_name] = price_data
                self.price_history.append(price_data)

            return price_data

        except ValueError as e:
            log_with_timestamp(f"✗ {e}")
            return None
        except Exception as e:
            log_with_timestamp(f"✗ Error fetching price from {exchange_name}: {e}")
            return None

    async def _fetch_price_generic(
        self, exchange_api: BaseExchangeAPI, trading_pair: str
    ) -> Optional[PriceData]:
        """Generic method to fetch price using any exchange API"""
        try:
            async with exchange_api as api:
                # Normalize trading pair for this exchange
                normalized_pair = api.normalize_pair(trading_pair)
                ticker_data = await api.get_ticker(normalized_pair)

                if ticker_data:
                    # Extract price data based on exchange type
                    exchange_name = api.get_exchange_name()

                    if exchange_name == "coinmate":
                        if not ticker_data.get("error", True):
                            data = ticker_data.get("data", {})
                            price = float(data.get("last", 0))
                            volume = float(data.get("amount", 0))
                        else:
                            error_msg = ticker_data.get("errorMessage", "Unknown error")
                            log_with_timestamp(
                                f"✗ {exchange_name.title()} API error: {error_msg}"
                            )
                            return None

                    elif exchange_name == "kraken":
                        if not ticker_data.get("error"):
                            result = ticker_data.get("result", {})
                            # Kraken uses different pair formats
                            pair_data = (
                                result.get(normalized_pair)
                                or result.get("XXBTZUSD")
                                or result.get("XBTUSD")
                                or result.get("BTCUSD")
                            )

                            if pair_data:
                                last_trade = pair_data.get("c", [None, None])
                                price = float(last_trade[0]) if last_trade[0] else None
                                volume = float(last_trade[1]) if last_trade[1] else 0.0

                                if not price:
                                    log_with_timestamp(
                                        f"✗ No price data in {exchange_name} response"
                                    )
                                    return None
                            else:
                                log_with_timestamp(
                                    f"✗ No pair data found for {normalized_pair} in {exchange_name}"
                                )
                                return None
                        else:
                            error_msg = ticker_data.get("error", "Unknown error")
                            log_with_timestamp(
                                f"✗ {exchange_name.title()} API error: {error_msg}"
                            )
                            return None
                    else:
                        log_with_timestamp(f"✗ Unsupported exchange: {exchange_name}")
                        return None

                    # Common processing for all exchanges
                    quote_currency = trading_pair.split("/")[1]

                    # Convert to USD if needed
                    price_usd = await self.currency_converter.convert_to_usd(
                        price, quote_currency
                    )
                    if price_usd is None:
                        log_with_timestamp(
                            f"⚠ Could not convert {quote_currency} to USD for {exchange_name}"
                        )
                        price_usd = price  # Fallback to original price

                    price_data = PriceData(
                        exchange=exchange_name,
                        symbol=trading_pair,
                        price=price,
                        price_usd=price_usd,
                        original_currency=quote_currency,
                        timestamp=time.time(),
                        volume=volume,
                    )

                    log_with_timestamp(
                        f"✓ {exchange_name.title()} API: {trading_pair} = {price} "
                        f"{quote_currency} (${price_usd:.2f} USD)"
                    )
                    return price_data
                else:
                    log_with_timestamp(
                        f"✗ No response from {exchange_api.get_exchange_name()} API"
                    )

        except Exception as e:
            log_with_timestamp(
                f"✗ {exchange_api.get_exchange_name().title()} API error: {e}"
            )

        return None

    def get_price_spread(self) -> Dict:
        if len(self.latest_prices) < 2:
            return {}

        # Use USD prices for comparison
        prices = [(name, data.price_usd) for name, data in self.latest_prices.items()]
        prices.sort(key=lambda x: x[1])

        lowest = prices[0]
        highest = prices[-1]

        spread = highest[1] - lowest[1]
        spread_percentage = (spread / lowest[1]) * 100

        # Get the exchange data for additional info
        lowest_data = self.latest_prices[lowest[0]]
        highest_data = self.latest_prices[highest[0]]

        return {
            "lowest": {
                "exchange": lowest[0],
                "price": lowest[1],
                "original_price": lowest_data.price,
                "currency": lowest_data.original_currency,
                "symbol": lowest_data.symbol,
            },
            "highest": {
                "exchange": highest[0],
                "price": highest[1],
                "original_price": highest_data.price,
                "currency": highest_data.original_currency,
                "symbol": highest_data.symbol,
            },
            "spread": spread,
            "spread_percentage": spread_percentage,
            "timestamp": time.time(),
        }

    def get_active_exchanges(self) -> List[str]:
        """Get list of exchanges that have provided price data"""
        return list(self.latest_prices.keys())

    async def close(self):
        """Close all exchange connections (not needed for direct API calls)"""
