"""
Abstract base class for cryptocurrency exchange APIs.

This module defines the interface that all exchange API implementations must follow,
ensuring consistency and making it easy to add new exchanges.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseExchangeAPI(ABC):
    """
    Abstract base class for cryptocurrency exchange APIs.

    All exchange API implementations (Kraken, Coinmate, Binance, etc.)
    must inherit from this class and implement the required methods.
    """

    def __init__(
        self, api_key: Optional[str] = None, api_secret: Optional[str] = None, **kwargs
    ):
        """
        Initialize the exchange API client.

        Args:
            api_key: API key for authenticated requests
            api_secret: API secret for authenticated requests
            **kwargs: Additional exchange-specific parameters (e.g., client_id for Coinmate)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = None

    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry - initialize session"""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup session"""

    # Core price/market data methods (required for arbitrage detection)

    @abstractmethod
    async def get_ticker(self, pair: str) -> Optional[Dict]:
        """
        Get ticker data for a trading pair.

        Args:
            pair: Trading pair (e.g., "BTCUSD", "BTC_CZK")

        Returns:
            Dict containing price data or None if error
        """

    @abstractmethod
    async def get_trading_fees(self, pair: str) -> Optional[float]:
        """
        Get trading fees for a specific trading pair.

        Args:
            pair: Trading pair (e.g., "BTCUSD", "BTC_CZK")

        Returns:
            Trading fee as percentage (e.g., 0.26 for 0.26%) or None if error
        """

    # Optional market data methods

    async def get_orderbook(self, pair: str, **kwargs) -> Optional[Dict]:
        """
        Get order book for a trading pair.

        Args:
            pair: Trading pair
            **kwargs: Exchange-specific parameters

        Returns:
            Order book data or None if not implemented/error
        """
        return None

    async def get_recent_trades(self, pair: str, **kwargs) -> Optional[Dict]:
        """
        Get recent trades for a trading pair.

        Args:
            pair: Trading pair
            **kwargs: Exchange-specific parameters

        Returns:
            Recent trades data or None if not implemented/error
        """
        return None

    # Authentication and account methods (optional)

    async def get_balance(self) -> Optional[Dict]:
        """
        Get account balance (requires authentication).

        Returns:
            Account balance data or None if not implemented/error
        """
        return None

    # Utility methods

    @abstractmethod
    def normalize_pair(self, pair: str) -> str:
        """
        Normalize trading pair format for this exchange.

        Args:
            pair: Trading pair in standard format (e.g., "BTC/USD")

        Returns:
            Exchange-specific pair format (e.g., "BTCUSD" for Kraken, "BTC_USD" for Coinmate)
        """

    @abstractmethod
    def get_exchange_name(self) -> str:
        """
        Get the name of this exchange.

        Returns:
            Exchange name (e.g., "kraken", "coinmate")
        """

    def is_authenticated(self) -> bool:
        """
        Check if API credentials are available.

        Returns:
            True if authenticated, False otherwise
        """
        return bool(self.api_key and self.api_secret)

    # Abstract methods for signature generation (each exchange has different auth)

    @abstractmethod
    def _generate_signature(self, *args, **kwargs) -> str:
        """
        Generate authentication signature for requests.
        Implementation varies by exchange.
        """

    @abstractmethod
    async def _make_request(
        self, endpoint: str, method: str = "GET", **kwargs
    ) -> Optional[Dict]:
        """
        Make HTTP request to exchange API.
        Implementation varies by exchange.
        """


# Factory function for creating exchange instances
def create_exchange_api(exchange_name: str, **kwargs) -> BaseExchangeAPI:
    """
    Factory function to create exchange API instances.

    Args:
        exchange_name: Name of the exchange ("kraken", "coinmate", etc.)
        **kwargs: API credentials and other parameters

    Returns:
        Exchange API instance

    Raises:
        ValueError: If exchange_name is not supported
    """
    if exchange_name.lower() == "kraken":
        from .kraken_api import KrakenAPI

        return KrakenAPI(kwargs.get("api_key"), kwargs.get("api_secret"))
    elif exchange_name.lower() == "coinmate":
        from .coinmate_api import CoinmateAPI

        return CoinmateAPI(
            kwargs.get("api_key"), kwargs.get("api_secret"), kwargs.get("client_id")
        )
    else:
        raise ValueError(f"Unsupported exchange: {exchange_name}")
