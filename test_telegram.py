#!/usr/bin/env python3
"""
Quick test script for Telegram bot functionality.
Run this to test your Telegram bot configuration.
"""

import asyncio
import os
from src.services.telegram_service import TelegramService
from src.core.arbitrage_detector import ArbitrageOpportunity
from dotenv import load_dotenv


async def main():
    # Load environment variables
    load_dotenv()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print("🧪 Testing Telegram Bot Configuration")
    print("=" * 50)

    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        return

    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID not found in environment variables")
        return

    print(f"✓ Bot Token: {bot_token[:10]}...{bot_token[-10:]}")
    print(f"✓ Chat ID: {chat_id}")
    print()

    # Initialize Telegram service
    telegram = TelegramService(bot_token, chat_id)

    if not telegram.enabled:
        print("❌ Telegram service is not enabled")
        return

    print("✓ Telegram service initialized")
    print()

    # Test 1: Basic connection test
    print("🔍 Test 1: Connection Test")
    success = await telegram.test_connection()
    if success:
        print("✅ Connection test passed!")
    else:
        print("❌ Connection test failed!")
        return
    print()

    # Test 2: Simple message
    print("🔍 Test 2: Simple Message")
    success = await telegram.send_message("Hello from Bitcoin Arbitrage Monitor! 🚀")
    if success:
        print("✅ Simple message sent successfully!")
    else:
        print("❌ Failed to send simple message!")
    print()

    # Test 3: System alert
    print("🔍 Test 3: System Alert")
    success = await telegram.send_system_alert(
        "🟢 System status: All monitoring services are operational"
    )
    if success:
        print("✅ System alert sent successfully!")
    else:
        print("❌ Failed to send system alert!")
    print()

    # Test 4: Mock arbitrage alert
    print("🔍 Test 4: Arbitrage Alert (Mock Data)")
    mock_opportunity = ArbitrageOpportunity(
        buy_exchange="coinmate",
        sell_exchange="kraken",
        buy_price=42000.0,
        sell_price=42350.0,
        profit_usd=350.0,
        profit_percentage=0.83,
        timestamp=1703254800.0,
        volume_limit=1.2500,
    )

    success = await telegram.send_arbitrage_alert(mock_opportunity)
    if success:
        print("✅ Arbitrage alert sent successfully!")
    else:
        print("❌ Failed to send arbitrage alert!")
    print()

    # Test 5: Markdown formatting test
    print("🔍 Test 5: Markdown Formatting")
    markdown_message = """🧪 *Markdown Test*

**Bold text**
_Italic text_
`Code text`
[Link](https://example.com)

• Bullet point 1
• Bullet point 2

That's all folks! 🎉"""

    success = await telegram.send_message(markdown_message)
    if success:
        print("✅ Markdown message sent successfully!")
    else:
        print("❌ Failed to send markdown message!")
    print()

    print("🎉 All tests completed!")
    print("Check your Telegram chat for the test messages.")


if __name__ == "__main__":
    asyncio.run(main())
