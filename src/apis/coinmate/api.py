import hashlib
import hmac
import time
from typing import Dict, Optional

import aiohttp

from ...utils.logging import log_with_timestamp
from ..base_exchange import BaseExchangeAPI


class CoinmateAPI(BaseExchangeAPI):
    """
    Coinmate API client for Czech cryptocurrency exchange
    Based on https://coinmate.docs.apiary.io/

    Args:
        api_key: Public key (publicKey in Coinmate terms)
        api_secret: Private key (privateKey in Coinmate terms)
        client_id: Client ID from account settings
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        client_id: Optional[str] = None,
    ):
        super().__init__(api_key, api_secret, client_id=client_id)
        self.base_url = "https://coinmate.io/api"
        self.client_id = client_id

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _generate_signature(self, nonce: str) -> str:
        """Generate HMAC-SHA256 signature for authenticated requests"""
        if not self.api_secret:
            raise ValueError("Private key required for authenticated requests")

        # Create message string: nonce + clientId + publicKey
        message = bytes(f"{nonce}{self.client_id}{self.api_key}", encoding="utf-8")
        private_key_bytes = bytes(self.api_secret, encoding="utf-8")
        signature = hmac.new(
            private_key_bytes, message, digestmod=hashlib.sha256
        ).hexdigest()
        return signature.upper()

    def get_exchange_name(self) -> str:
        """Get the name of this exchange"""
        return "coinmate"

    def normalize_pair(self, pair: str) -> str:
        """Convert BTC/USD to BTC_USD format for Coinmate"""
        return pair.replace("/", "_")

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

            # Use seconds for nonce as in signature.py
            nonce = str(int(time.time()))
            signature = self._generate_signature(nonce)

            data = data or {}
            data.update(
                {
                    "clientId": self.client_id,
                    "publicKey": self.api_key,
                    "nonce": nonce,
                    "signature": signature,
                }
            )

        try:
            if method == "GET":
                async with self.session.get(url, params=data) as response:
                    if response.status == 200:
                        return await response.json()
            elif method == "POST":
                # Use proper headers for form data as in working implementation
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                async with self.session.post(
                    url, data=data, headers=headers
                ) as response:
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

    async def get_trading_fees(self, currency_pair: str = "BTC_CZK") -> Optional[float]:
        """
        Get trading fees for a specific currency pair

        Note: The tradingFees endpoint from the Coinmate documentation appears to be
        unavailable (returns 404). This function attempts to fetch fees but will
        return None if the endpoint is not available, allowing fallback to configured fees.

        Based on: https://coinmate.docs.apiary.io/#reference/trader-fees/get-trading-fees
        """
        if not all([self.api_key, self.api_secret, self.client_id]):
            log_with_timestamp(
                "⚠ Coinmate API credentials missing, cannot fetch trading fees"
            )
            return None

        try:
            endpoint = "traderFees"
            # Send currencyPair - API returns fees for the specific pair
            data = {"currencyPair": currency_pair}
            fees_data = await self._make_request(
                endpoint, "POST", data, auth_required=True
            )

            if fees_data and not fees_data.get("error", True):
                data = fees_data.get("data", {})

                # API returns fees directly: {"maker": 0.35, "taker": 0.5, "timestamp": ...}
                if "taker" in data:
                    taker_fee = data["taker"]
                    return float(taker_fee)
                else:
                    log_with_timestamp(
                        f"⚠ No taker fee found for {currency_pair} in Coinmate API response: {data}"
                    )
                    return None
            else:
                # Don't log 404 errors as they're expected for this endpoint
                if fees_data is None:
                    log_with_timestamp(
                        "⚠ Coinmate traderFees endpoint not available (404)"
                    )
                else:
                    error_msg = fees_data.get("errorMessage", "Unknown error")
                    if "Access denied" in str(error_msg):
                        log_with_timestamp(
                            "⚠ Coinmate API access denied - check credentials and permissions"
                        )
                    else:
                        log_with_timestamp(
                            f"✗ Coinmate trading fees API error: {error_msg}"
                        )
                return None

        except Exception as e:
            log_with_timestamp(f"✗ Coinmate fee fetch error: {e}")
        return None

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
