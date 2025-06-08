import hashlib
import hmac
import time
from typing import Any, Dict, Optional

import aiohttp

from ..utils.logging import log_with_timestamp


class CoinmateAPI:
    """
    Coinmate API client for Czech cryptocurrency exchange
    Based on https://coinmate.docs.apiary.io/
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        client_id: Optional[str] = None,
    ):
        self.base_url = "https://coinmate.io/api"
        self.api_key = api_key
        self.api_secret = api_secret
        self.client_id = client_id
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _generate_signature(self, nonce: str, data: Dict[str, Any]) -> str:
        """Generate HMAC-SHA256 signature for authenticated requests"""
        if not self.api_secret:
            raise ValueError("API secret required for authenticated requests")

        # Create message string
        message = f"{nonce}{self.client_id}{self.api_key}"

        # Add sorted data parameters
        for key in sorted(data.keys()):
            message += f"{key}={data[key]}"

        # Generate signature
        signature = (
            hmac.new(
                self.api_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
            )
            .hexdigest()
            .upper()
        )

        return signature

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        auth_required: bool = False,
    ) -> Optional[Dict]:
        """Make request to Coinmate API"""
        url = f"{self.base_url}/{endpoint}"

        if auth_required:
            if not all([self.api_key, self.api_secret, self.client_id]):
                raise ValueError("API credentials required for authenticated requests")

            nonce = str(int(time.time() * 1000))
            data = data or {}
            data.update(
                {"clientId": self.client_id, "publicKey": self.api_key, "nonce": nonce}
            )
            data["signature"] = self._generate_signature(nonce, data)

        try:
            if method == "GET":
                async with self.session.get(url, params=data) as response:
                    if response.status == 200:
                        return await response.json()
            elif method == "POST":
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        return await response.json()

        except Exception as e:
            log_with_timestamp(f"✗ Coinmate API error: {e}")
            return None

    async def get_ticker(self, currency_pair: str = "BTC_CZK") -> Optional[Dict]:
        """
        Get ticker data for a currency pair
        Public endpoint - no authentication required
        """
        endpoint = "ticker"
        data = {"currencyPair": currency_pair}
        return await self._make_request(endpoint, "GET", data, auth_required=False)

    async def get_orderbook(self, currency_pair: str = "BTC_CZK") -> Optional[Dict]:
        """
        Get order book for a currency pair
        Public endpoint - no authentication required
        """
        endpoint = "orderBook"
        data = {"currencyPair": currency_pair}
        return await self._make_request(endpoint, "GET", data, auth_required=False)

    async def get_transactions(
        self, currency_pair: str = "BTC_CZK", minutes_into_past: int = 60
    ) -> Optional[Dict]:
        """
        Get recent transactions
        Public endpoint - no authentication required
        """
        endpoint = "transactions"
        data = {"currencyPair": currency_pair, "minutesIntoHistory": minutes_into_past}
        return await self._make_request(endpoint, "GET", data, auth_required=False)

    async def get_trading_pairs(self) -> Optional[Dict]:
        """
        Get available trading pairs
        Public endpoint - no authentication required
        """
        endpoint = "tradingPairs"
        return await self._make_request(endpoint, "GET", auth_required=False)

    # Authenticated endpoints (require API credentials)

    async def get_balance(self) -> Optional[Dict]:
        """
        Get account balance
        Requires authentication
        """
        endpoint = "balances"
        return await self._make_request(endpoint, "POST", auth_required=True)

    async def create_buy_order(
        self, amount: float, price: float, currency_pair: str = "BTC_CZK"
    ) -> Optional[Dict]:
        """
        Create buy order
        Requires authentication
        """
        endpoint = "buyLimit"
        data = {"amount": amount, "price": price, "currencyPair": currency_pair}
        return await self._make_request(endpoint, "POST", data, auth_required=True)

    async def create_sell_order(
        self, amount: float, price: float, currency_pair: str = "BTC_CZK"
    ) -> Optional[Dict]:
        """
        Create sell order
        Requires authentication
        """
        endpoint = "sellLimit"
        data = {"amount": amount, "price": price, "currencyPair": currency_pair}
        return await self._make_request(endpoint, "POST", data, auth_required=True)

    async def cancel_order(self, order_id: int) -> Optional[Dict]:
        """
        Cancel order
        Requires authentication
        """
        endpoint = "cancelOrder"
        data = {"orderId": order_id}
        return await self._make_request(endpoint, "POST", data, auth_required=True)

    async def get_order_history(
        self, currency_pair: str = "BTC_CZK", limit: int = 100
    ) -> Optional[Dict]:
        """
        Get order history
        Requires authentication
        """
        endpoint = "orderHistory"
        data = {"currencyPair": currency_pair, "limit": limit}
        return await self._make_request(endpoint, "POST", data, auth_required=True)


# Utility function for easy ticker access
async def get_coinmate_btc_czk_price() -> Optional[float]:
    """Get current BTC/CZK price from Coinmate"""
    async with CoinmateAPI() as api:
        ticker_data = await api.get_ticker("BTC_CZK")
        if ticker_data and not ticker_data.get("error", True):
            data = ticker_data.get("data", {})
            return float(data.get("last", 0))
    return None
