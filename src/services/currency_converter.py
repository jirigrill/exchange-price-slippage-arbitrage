import aiohttp
from typing import Dict, Optional
import time
from ..utils.logging import log_with_timestamp


class CurrencyConverter:
    def __init__(self):
        self.exchange_rates = {}
        self.last_update = 0
        self.cache_duration = 300  # 5 minutes

    async def get_exchange_rate(
        self, from_currency: str, to_currency: str = "USD"
    ) -> Optional[float]:
        """Get exchange rate from one currency to another (default to USD)"""
        if from_currency == to_currency:
            return 1.0

        # USDT is considered equivalent to USD
        if from_currency == "USDT" and to_currency == "USD":
            return 1.0
        if from_currency == "USD" and to_currency == "USDT":
            return 1.0

        # Check if we need to update rates
        if time.time() - self.last_update > self.cache_duration:
            await self._update_exchange_rates()

        rate_key = f"{from_currency}/{to_currency}"
        return self.exchange_rates.get(rate_key)

    async def _update_exchange_rates(self):
        """Update exchange rates from API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Using exchangerate-api.com (free tier)
                url = "https://api.exchangerate-api.com/v4/latest/USD"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get("rates", {})

                        # Store USD rates
                        for currency, rate in rates.items():
                            self.exchange_rates[f"USD/{currency}"] = rate
                            if rate != 0:
                                self.exchange_rates[f"{currency}/USD"] = 1.0 / rate

                        # Calculate cross rates for common pairs
                        if "CZK" in rates and "EUR" in rates:
                            czk_to_eur = rates["EUR"] / rates["CZK"]
                            self.exchange_rates["CZK/EUR"] = czk_to_eur
                            self.exchange_rates["EUR/CZK"] = 1.0 / czk_to_eur

                        self.last_update = time.time()
                        log_with_timestamp(
                            f"✓ Updated exchange rates (CZK/USD: {self.exchange_rates.get('CZK/USD', 'N/A'):.4f})"
                        )

        except Exception as e:
            log_with_timestamp(f"✗ Error updating exchange rates: {e}")

    async def convert_to_usd(
        self, amount: float, from_currency: str
    ) -> Optional[float]:
        """Convert amount from given currency to USD"""
        if from_currency == "USD" or from_currency == "USDT":
            return amount

        rate = await self.get_exchange_rate(from_currency, "USD")
        if rate is not None:
            return amount * rate
        return None
