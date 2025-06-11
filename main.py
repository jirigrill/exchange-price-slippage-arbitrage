import asyncio
import sys

from config.settings import (
    ALL_EXCHANGES,
    API_KEYS,
    COINMATE_TRADING_FEE,
    DATABASE_ENABLED,
    DATABASE_URL,
    DYNAMIC_FEES_ENABLED,
    EXCHANGE_TRADING_PAIRS,
    KRAKEN_TRADING_FEE,
    MIN_PROFIT_PERCENTAGE,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_ENABLED,
    TRADING_SYMBOL,
)
from src.core.arbitrage_detector import ArbitrageDetector
from src.core.exchange_monitor import ExchangeMonitor
from src.services.database_service import DatabaseService
from src.services.telegram_service import TelegramService
from src.utils.logging import log_with_timestamp


async def main():
    log_with_timestamp("🚀 Starting Bitcoin Latency Arbitrage POC...")
    log_with_timestamp(f"📊 Monitoring exchanges: {ALL_EXCHANGES}")
    log_with_timestamp(f"💰 Trading symbol: {TRADING_SYMBOL}")
    log_with_timestamp(f"📈 Minimum profit threshold: {MIN_PROFIT_PERCENTAGE}%")

    # Log fee configuration
    if DYNAMIC_FEES_ENABLED:
        log_with_timestamp("⚡ Dynamic fees: enabled (fetching from exchange APIs)")
        log_with_timestamp(
            f"📊 Fallback fees: Kraken {KRAKEN_TRADING_FEE}%, Coinmate {COINMATE_TRADING_FEE}%"
        )
    else:
        log_with_timestamp("📊 Static fees: enabled")
        log_with_timestamp(
            f"📊 Trading fees: Kraken {KRAKEN_TRADING_FEE}%, Coinmate {COINMATE_TRADING_FEE}%"
        )

    if TELEGRAM_ENABLED:
        log_with_timestamp(
            f"📱 Telegram alerts: enabled for all opportunities >= {MIN_PROFIT_PERCENTAGE}%"
        )
    else:
        log_with_timestamp("📱 Telegram alerts: disabled")

    if DATABASE_ENABLED:
        log_with_timestamp("📊 Database: enabled (TimescaleDB)")
    else:
        log_with_timestamp("📊 Database: disabled")

    print("-" * 50)

    # Force flush output
    sys.stdout.flush()

    # Initialize database service
    database_service = DatabaseService(DATABASE_URL, DATABASE_ENABLED)
    if not await database_service.initialize():
        log_with_timestamp(
            "⚠ Database initialization failed - continuing without database"
        )
        database_service = None

    # Initialize services
    monitor = ExchangeMonitor(
        ALL_EXCHANGES,
        EXCHANGE_TRADING_PAIRS,
        API_KEYS,
        TRADING_SYMBOL,
        database_service,
    )
    detector = ArbitrageDetector(monitor, MIN_PROFIT_PERCENTAGE, database_service)
    telegram = TelegramService(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED)

    # Test Telegram connection if enabled
    if telegram.enabled:
        await telegram.test_connection()
    elif TELEGRAM_ENABLED and (not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID):
        log_with_timestamp("⚠ Telegram enabled but missing BOT_TOKEN or CHAT_ID")

    async def monitor_and_detect():
        while True:
            try:
                tasks = []
                for exchange_name in monitor.exchanges:
                    tasks.append(monitor.fetch_price(exchange_name))

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                opportunities = await detector.detect_opportunities()

                if opportunities:
                    log_with_timestamp(
                        f"🚨 Found {len(opportunities)} arbitrage opportunities:"
                    )

                    # Send Telegram alerts for all detected opportunities
                    if telegram.enabled:
                        for opp in opportunities:
                            await telegram.send_arbitrage_alert(opp)

                    # Log opportunities to console
                    for i, opp in enumerate(opportunities[:3], 1):
                        gross_profit = (
                            (opp.sell_price - opp.buy_price) / opp.buy_price
                        ) * 100
                        trading_fees = gross_profit - opp.profit_percentage

                        log_with_timestamp(
                            f"{i}. Buy on {opp.buy_exchange} at ${opp.buy_price:.2f}"
                        )
                        log_with_timestamp(
                            f"   Sell on {opp.sell_exchange} at ${opp.sell_price:.2f}"
                        )
                        log_with_timestamp(
                            f"   Gross profit: {gross_profit:.2f}% | Trading fees: {trading_fees:.2f}%"  # noqa: E501
                        )
                        log_with_timestamp(
                            f"   Net profit: ${opp.profit_usd:.2f} ({opp.profit_percentage:.2f}%)"
                        )
                        log_with_timestamp(
                            f"   Volume limit: {opp.volume_limit:.4f} BTC"
                        )
                        if telegram.enabled:
                            log_with_timestamp("   📱 Telegram alert sent!")
                        else:
                            log_with_timestamp("   📱 Telegram alerts disabled")
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

    try:
        await monitor_and_detect()
    finally:
        # Cleanup database connection
        if database_service:
            await database_service.close()


if __name__ == "__main__":
    asyncio.run(main())
