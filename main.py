import asyncio
import sys

from config.settings import (
    ALL_EXCHANGES,
    API_KEYS,
    EXCHANGE_TRADING_PAIRS,
    MIN_PROFIT_PERCENTAGE,
    TELEGRAM_ALERT_THRESHOLD,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TRADING_SYMBOL,
)
from src.core.arbitrage_detector import ArbitrageDetector
from src.core.exchange_monitor import ExchangeMonitor
from src.services.telegram_service import TelegramService
from src.utils.logging import log_with_timestamp


async def main():
    log_with_timestamp("🚀 Starting Bitcoin Latency Arbitrage POC...")
    log_with_timestamp(f"📊 Monitoring exchanges: {ALL_EXCHANGES}")
    log_with_timestamp(f"💰 Trading symbol: {TRADING_SYMBOL}")
    log_with_timestamp(f"📈 Minimum profit threshold: {MIN_PROFIT_PERCENTAGE}%")
    log_with_timestamp(f"📱 Telegram alert threshold: {TELEGRAM_ALERT_THRESHOLD}%")
    print("-" * 50)

    # Force flush output
    sys.stdout.flush()

    # Initialize services
    monitor = ExchangeMonitor(
        ALL_EXCHANGES, EXCHANGE_TRADING_PAIRS, API_KEYS, TRADING_SYMBOL
    )
    detector = ArbitrageDetector(monitor, MIN_PROFIT_PERCENTAGE)
    telegram = TelegramService(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

    # Test Telegram connection if enabled
    if telegram.enabled:
        await telegram.test_connection()

    async def monitor_and_detect():
        while True:
            try:
                tasks = []
                for exchange_name in monitor.exchanges:
                    tasks.append(monitor.fetch_price(exchange_name))

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                opportunities = detector.detect_opportunities()

                if opportunities:
                    log_with_timestamp(
                        f"🚨 Found {len(opportunities)} arbitrage opportunities:"
                    )

                    # Send Telegram alerts for high-profit opportunities
                    for opp in opportunities:
                        if opp.profit_percentage >= TELEGRAM_ALERT_THRESHOLD:
                            await telegram.send_arbitrage_alert(opp)

                    # Log opportunities to console
                    for i, opp in enumerate(opportunities[:3], 1):
                        log_with_timestamp(
                            f"{i}. Buy on {opp.buy_exchange} at ${opp.buy_price:.2f}"
                        )
                        log_with_timestamp(
                            f"   Sell on {opp.sell_exchange} at ${opp.sell_price:.2f}"
                        )
                        log_with_timestamp(
                            f"   Profit: ${opp.profit_usd:.2f} ({opp.profit_percentage:.2f}%)"
                        )
                        log_with_timestamp(
                            f"   Volume limit: {opp.volume_limit:.4f} BTC"
                        )
                        if opp.profit_percentage >= TELEGRAM_ALERT_THRESHOLD:
                            log_with_timestamp("   📱 Telegram alert sent!")
                        print()

                spread_data = monitor.get_price_spread()
                if spread_data:
                    active_exchanges = monitor.get_active_exchanges()
                    all_exchanges = monitor.exchanges

                    log_with_timestamp(
                        f"Active exchanges "
                        f"({len(active_exchanges)}/{len(all_exchanges)}): "
                        f"{', '.join(active_exchanges)}"
                    )

                    log_with_timestamp(
                        f"Current spread: ${spread_data['spread']:.2f} "
                        f"({spread_data['spread_percentage']:.2f}%)"
                    )

                    lowest = spread_data["lowest"]
                    highest = spread_data["highest"]
                    log_with_timestamp(
                        f"Lowest: {lowest['exchange']} - " f"${lowest['price']:.2f} USD"
                    )
                    log_with_timestamp(
                        f"Highest: {highest['exchange']} - "
                        f"${highest['price']:.2f} USD"
                    )
                else:
                    active_exchanges = monitor.get_active_exchanges()
                    all_exchanges = monitor.exchanges
                    inactive_exchanges = [
                        ex for ex in all_exchanges if ex not in active_exchanges
                    ]

                    log_with_timestamp(
                        f"Active exchanges "
                        f"({len(active_exchanges)}/{len(all_exchanges)}): "
                        f"{', '.join(active_exchanges)}"
                    )
                    if inactive_exchanges:
                        log_with_timestamp(
                            f"Inactive exchanges: {', '.join(inactive_exchanges)}"
                        )
                    log_with_timestamp("No spread data available yet...")

                await asyncio.sleep(5)

            except KeyboardInterrupt:
                log_with_timestamp("Stopping arbitrage monitor...")
                break
            except Exception as e:
                log_with_timestamp(f"Error in monitoring loop: {e}")
                await asyncio.sleep(1)

    await monitor_and_detect()


if __name__ == "__main__":
    asyncio.run(main())
