from typing import Optional

import aiohttp

from ..utils.logging import log_with_timestamp


class TelegramService:
    """
    Telegram bot service for sending alerts about arbitrage opportunities
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        enabled: bool = True,
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = (
            f"https://api.telegram.org/bot{bot_token}" if bot_token else None
        )

        # Determine why Telegram might be disabled
        has_credentials = bool(bot_token and chat_id)
        self.enabled = enabled and has_credentials

        # Provide specific feedback about why Telegram is enabled/disabled
        if self.enabled:
            log_with_timestamp("✓ Telegram notifications enabled")
        elif not enabled:
            log_with_timestamp(
                "⚠ Telegram notifications disabled (TELEGRAM_ENABLED=false)"
            )
        elif not has_credentials:
            missing_items = []
            if not bot_token:
                missing_items.append("BOT_TOKEN")
            if not chat_id:
                missing_items.append("CHAT_ID")
            log_with_timestamp(
                f"⚠ Telegram notifications disabled (missing {', '.join(missing_items)})"
            )
        else:
            log_with_timestamp("⚠ Telegram notifications disabled (unknown reason)")

    async def send_message(self, message: str) -> bool:
        """Send a message to the configured Telegram chat"""
        if not self.enabled:
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        log_with_timestamp("✓ Telegram message sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        log_with_timestamp(
                            f"✗ Telegram API error: {response.status} - "
                            f"{error_text}"
                        )
                        return False

        except Exception as e:
            log_with_timestamp(f"✗ Error sending Telegram message: {e}")
            return False

    async def send_arbitrage_alert(self, opportunity) -> bool:
        """Send formatted arbitrage opportunity alert"""
        if not self.enabled:
            return False

        # Format the message with arbitrage details
        message = f"""🚨 *Arbitrage Opportunity Detected!*

💰 *Profit*: ${opportunity.profit_usd:.2f} \
({opportunity.profit_percentage:.2f}%)
📈 *Buy*: {opportunity.buy_exchange} @ ${opportunity.buy_price:.2f}
📉 *Sell*: {opportunity.sell_exchange} @ ${opportunity.sell_price:.2f}
📊 *Volume Limit*: {opportunity.volume_limit:.4f} BTC

⚡ Act quickly - prices change rapidly!"""

        return await self.send_message(message)

    async def send_system_alert(self, message: str) -> bool:
        """Send system status or error alerts"""
        if not self.enabled:
            return False

        formatted_message = f"🤖 *Bitcoin Arbitrage Monitor*\n\n{message}"
        return await self.send_message(formatted_message)

    async def test_connection(self) -> bool:
        """Test the Telegram bot connection"""
        if not self.enabled:
            log_with_timestamp("Cannot test Telegram - bot not configured")
            return False

        test_message = (
            "🧪 *Test Message*\n\n" "Bitcoin Arbitrage Monitor is online and ready!"
        )
        success = await self.send_message(test_message)

        if success:
            log_with_timestamp("✓ Telegram connection test successful")
        else:
            log_with_timestamp("✗ Telegram connection test failed")

        return success
