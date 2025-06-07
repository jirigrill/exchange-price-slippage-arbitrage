import aiohttp
import hashlib
import hmac
import time
import base64
import urllib.parse
from typing import Dict, Optional, Any


class KrakenAPI:
    """
    Kraken API client for cryptocurrency exchange
    Based on https://docs.kraken.com/api/
    """

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.base_url = "https://api.kraken.com"
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _generate_signature(
        self, url_path: str, data: Dict[str, Any], nonce: str
    ) -> str:
        """Generate signature for authenticated requests"""
        if not self.api_secret:
            raise ValueError("API secret required for authenticated requests")

        # Create the message
        post_data = urllib.parse.urlencode(data)
        encoded = (nonce + post_data).encode("utf-8")
        message = url_path.encode("utf-8") + hashlib.sha256(encoded).digest()

        # Generate signature
        signature = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)

        return base64.b64encode(signature.digest()).decode("utf-8")

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        auth_required: bool = False,
    ) -> Optional[Dict]:
        """Make request to Kraken API"""
        url = f"{self.base_url}/{endpoint}"

        headers = {}

        if auth_required:
            if not all([self.api_key, self.api_secret]):
                raise ValueError("API credentials required for authenticated requests")

            nonce = str(int(time.time() * 1000))
            data = data or {}
            data["nonce"] = nonce

            url_path = f"/{endpoint}"
            signature = self._generate_signature(url_path, data, nonce)

            headers.update(
                {
                    "API-Key": self.api_key,
                    "API-Sign": signature,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            )

        try:
            if method == "GET":
                async with self.session.get(url, params=data) as response:
                    if response.status == 200:
                        return await response.json()
            elif method == "POST":
                if auth_required:
                    post_data = urllib.parse.urlencode(data)
                    async with self.session.post(
                        url, data=post_data, headers=headers
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                else:
                    async with self.session.post(url, json=data) as response:
                        if response.status == 200:
                            return await response.json()

        except Exception as e:
            print(f"✗ Kraken API error: {e}")
            return None

    async def get_ticker(self, pair: str = "BTCUSD") -> Optional[Dict]:
        """
        Get ticker data for a trading pair
        Public endpoint - no authentication required
        """
        endpoint = "0/public/Ticker"
        data = {"pair": pair} if pair else None
        return await self._make_request(endpoint, "GET", data, auth_required=False)

    async def get_ohlc(self, pair: str = "BTCUSD", interval: int = 1) -> Optional[Dict]:
        """
        Get OHLC (Open, High, Low, Close) data
        Public endpoint - no authentication required
        """
        endpoint = "0/public/OHLC"
        data = {"pair": pair, "interval": interval}
        return await self._make_request(endpoint, "GET", data, auth_required=False)

    async def get_order_book(
        self, pair: str = "BTCUSD", count: int = 100
    ) -> Optional[Dict]:
        """
        Get order book data
        Public endpoint - no authentication required
        """
        endpoint = "0/public/Depth"
        data = {"pair": pair, "count": count}
        return await self._make_request(endpoint, "GET", data, auth_required=False)

    async def get_recent_trades(
        self, pair: str = "BTCUSD", since: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get recent trades
        Public endpoint - no authentication required
        """
        endpoint = "0/public/Trades"
        data = {"pair": pair}
        if since:
            data["since"] = since
        return await self._make_request(endpoint, "GET", data, auth_required=False)

    async def get_asset_pairs(self) -> Optional[Dict]:
        """
        Get available asset pairs
        Public endpoint - no authentication required
        """
        endpoint = "0/public/AssetPairs"
        return await self._make_request(endpoint, "GET", auth_required=False)

    # Authenticated endpoints (require API credentials)

    async def get_account_balance(self) -> Optional[Dict]:
        """
        Get account balance
        Requires authentication
        """
        endpoint = "0/private/Balance"
        return await self._make_request(endpoint, "POST", {}, auth_required=True)

    async def get_open_orders(self) -> Optional[Dict]:
        """
        Get open orders
        Requires authentication
        """
        endpoint = "0/private/OpenOrders"
        return await self._make_request(endpoint, "POST", {}, auth_required=True)

    async def add_order(
        self,
        pair: str,
        type_: str,
        ordertype: str,
        volume: str,
        price: Optional[str] = None,
        **kwargs,
    ) -> Optional[Dict]:
        """
        Add order
        Requires authentication

        Args:
            pair: Asset pair
            type_: Order type ('buy' or 'sell')
            ordertype: Order type ('market', 'limit', etc.)
            volume: Order volume
            price: Order price (required for limit orders)
        """
        endpoint = "0/private/AddOrder"
        data = {"pair": pair, "type": type_, "ordertype": ordertype, "volume": volume}

        if price:
            data["price"] = price

        data.update(kwargs)

        return await self._make_request(endpoint, "POST", data, auth_required=True)

    async def cancel_order(self, txid: str) -> Optional[Dict]:
        """
        Cancel order
        Requires authentication
        """
        endpoint = "0/private/CancelOrder"
        data = {"txid": txid}
        return await self._make_request(endpoint, "POST", data, auth_required=True)

    async def get_closed_orders(
        self, start: Optional[str] = None, end: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get closed orders
        Requires authentication
        """
        endpoint = "0/private/ClosedOrders"
        data = {}
        if start:
            data["start"] = start
        if end:
            data["end"] = end
        return await self._make_request(endpoint, "POST", data, auth_required=True)


# Utility function for easy ticker access
async def get_kraken_btc_usd_price() -> Optional[float]:
    """Get current BTC/USD price from Kraken"""
    async with KrakenAPI() as api:
        ticker_data = await api.get_ticker("BTCUSD")
        if ticker_data and not ticker_data.get("error"):
            result = ticker_data.get("result", {})
            # Kraken returns different pair names, try both BTCUSD and XBTUSD
            btc_data = result.get("BTCUSD") or result.get("XBTUSD")
            if btc_data:
                # 'c' contains [price, volume] for last trade
                last_price = btc_data.get("c", [None])[0]
                if last_price:
                    return float(last_price)
    return None
