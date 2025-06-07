import time
from typing import Dict, List, Optional
import ccxt.async_support as ccxt
from dataclasses import dataclass
from .currency_converter import CurrencyConverter
from .coinmate_api import CoinmateAPI
from .kraken_api import KrakenAPI


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
        self.exchange_instances = {}
        self.latest_prices = {}
        self.price_history = []
        self.currency_converter = CurrencyConverter()

        for exchange_name in exchanges:
            try:
                exchange_class = getattr(ccxt, exchange_name)
                config = {
                    "enableRateLimit": True,
                }

                exchange_instance = exchange_class(config)

                if hasattr(exchange_instance, "sandbox") and exchange_instance.urls.get(
                    "test"
                ):
                    try:
                        exchange_instance.set_sandbox_mode(True)
                        print(f"✓ Enabled sandbox mode for {exchange_name}")
                    except:
                        print(
                            f"⚠ Sandbox mode not available for {exchange_name}, using live API"
                        )

                self.exchange_instances[exchange_name] = exchange_instance
                print(f"✓ Initialized {exchange_name}")

            except AttributeError:
                print(f"✗ Exchange {exchange_name} not supported by ccxt")
            except Exception as e:
                print(f"✗ Error initializing {exchange_name}: {e}")

    async def fetch_price(self, exchange_name: str) -> Optional[PriceData]:
        # Get the trading pair for this exchange
        trading_pair = self.trading_pairs.get(exchange_name, self.symbol)

        # Use specialized APIs for specific exchanges
        if exchange_name == "coinmate":
            price_data = await self._fetch_price_coinmate_api(trading_pair)
        elif exchange_name == "kraken":
            price_data = await self._fetch_price_kraken_api(trading_pair)
        else:
            # Use CCXT for other exchanges
            price_data = await self._fetch_price_ccxt(exchange_name, trading_pair)

        if price_data:
            self.latest_prices[exchange_name] = price_data
            self.price_history.append(price_data)

        return price_data

    async def _fetch_price_ccxt(
        self, exchange_name: str, trading_pair: str
    ) -> Optional[PriceData]:
        """Fetch price using CCXT library"""
        try:
            if exchange_name not in self.exchange_instances:
                return None

            exchange = self.exchange_instances[exchange_name]
            ticker = await exchange.fetch_ticker(trading_pair)

            price = ticker["last"]
            quote_currency = trading_pair.split("/")[1]

            # Convert to USD if needed
            price_usd = await self.currency_converter.convert_to_usd(
                price, quote_currency
            )
            if price_usd is None:
                print(
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
                volume=ticker.get("baseVolume", 0),
            )

            return price_data

        except Exception as e:
            print(f"✗ CCXT error for {exchange_name}: {e}")
            return None

    async def _fetch_price_coinmate_api(self, trading_pair: str) -> Optional[PriceData]:
        """Fetch price using Coinmate API directly"""
        try:
            # Get API credentials if available
            coinmate_creds = self.api_keys.get("coinmate", {})
            api_key = coinmate_creds.get("apiKey")
            api_secret = coinmate_creds.get("secret")
            client_id = coinmate_creds.get("clientId")

            async with CoinmateAPI(api_key, api_secret, client_id) as api:
                # Convert trading pair format (BTC/CZK -> BTC_CZK)
                coinmate_pair = trading_pair.replace("/", "_")
                ticker_data = await api.get_ticker(coinmate_pair)

                if ticker_data and not ticker_data.get("error", True):
                    data = ticker_data.get("data", {})
                    price = float(data.get("last", 0))
                    quote_currency = trading_pair.split("/")[1]

                    # Convert to USD if needed
                    price_usd = await self.currency_converter.convert_to_usd(
                        price, quote_currency
                    )
                    if price_usd is None:
                        print(
                            f"⚠ Could not convert {quote_currency} to USD for coinmate"
                        )
                        price_usd = price  # Fallback to original price

                    price_data = PriceData(
                        exchange="coinmate",
                        symbol=trading_pair,
                        price=price,
                        price_usd=price_usd,
                        original_currency=quote_currency,
                        timestamp=time.time(),
                        volume=float(data.get("amount", 0)),
                    )

                    print(
                        f"✓ Coinmate API: {trading_pair} = {price} {quote_currency} (${price_usd:.2f} USD)"
                    )
                    return price_data
                else:
                    error_msg = (
                        ticker_data.get("errorMessage", "Unknown error")
                        if ticker_data
                        else "No response"
                    )
                    print(f"✗ Coinmate API error: {error_msg}")

        except Exception as e:
            print(f"✗ Coinmate API error: {e}")

        return None

    async def _fetch_price_kraken_api(self, trading_pair: str) -> Optional[PriceData]:
        """Fetch price using Kraken API directly"""
        try:
            # Get API credentials if available
            kraken_creds = self.api_keys.get("kraken", {})
            api_key = kraken_creds.get("apiKey")
            api_secret = kraken_creds.get("secret")

            async with KrakenAPI(api_key, api_secret) as api:
                # Convert trading pair format (BTC/USD -> BTCUSD)
                kraken_pair = trading_pair.replace("/", "")
                ticker_data = await api.get_ticker(kraken_pair)

                if ticker_data and not ticker_data.get("error"):
                    result = ticker_data.get("result", {})

                    # Kraken uses different pair formats: XXBTZUSD, XBTUSD, BTCUSD
                    pair_data = (
                        result.get(kraken_pair)
                        or result.get("XXBTZUSD")
                        or result.get("XBTUSD")
                        or result.get("BTCUSD")
                    )

                    if pair_data:
                        # 'c' contains [price, volume] for last trade
                        last_trade = pair_data.get("c", [None, None])
                        price = float(last_trade[0]) if last_trade[0] else None
                        volume = float(last_trade[1]) if last_trade[1] else 0.0

                        if price:
                            quote_currency = trading_pair.split("/")[1]

                            # Convert to USD if needed
                            price_usd = await self.currency_converter.convert_to_usd(
                                price, quote_currency
                            )
                            if price_usd is None:
                                print(
                                    f"⚠ Could not convert {quote_currency} to USD for kraken"
                                )
                                price_usd = price  # Fallback to original price

                            price_data = PriceData(
                                exchange="kraken",
                                symbol=trading_pair,
                                price=price,
                                price_usd=price_usd,
                                original_currency=quote_currency,
                                timestamp=time.time(),
                                volume=volume,
                            )

                            print(
                                f"✓ Kraken API: {trading_pair} = {price} {quote_currency} (${price_usd:.2f} USD)"
                            )
                            return price_data
                else:
                    error_msg = (
                        ticker_data.get("error", "Unknown error")
                        if ticker_data
                        else "No response"
                    )
                    print(f"✗ Kraken API error: {error_msg}")

        except Exception as e:
            print(f"✗ Kraken API error: {e}")

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

    def get_initialized_exchanges(self) -> List[str]:
        """Get list of exchanges that were successfully initialized"""
        return list(self.exchange_instances.keys())

    async def close(self):
        """Close all exchange connections"""
        for exchange in self.exchange_instances.values():
            if hasattr(exchange, "close"):
                await exchange.close()
