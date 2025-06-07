import asyncio
from src.core.exchange_monitor import ExchangeMonitor
from src.core.arbitrage_detector import ArbitrageDetector
from src.utils.logging import log_with_timestamp
from config.settings import (
    ALL_EXCHANGES,
    TRADING_SYMBOL,
    MIN_PROFIT_PERCENTAGE,
    EXCHANGE_TRADING_PAIRS,
    API_KEYS,
)

async def main():
    log_with_timestamp("🚀 Starting Bitcoin Latency Arbitrage POC...")
    log_with_timestamp(f"📊 Monitoring exchanges: {ALL_EXCHANGES}")
    log_with_timestamp(f"💰 Trading symbol: {TRADING_SYMBOL}")
    log_with_timestamp(f"📈 Minimum profit threshold: {MIN_PROFIT_PERCENTAGE}%")
    print("-" * 50)
    
    # Force flush output
    import sys
    sys.stdout.flush()

    monitor = ExchangeMonitor(
        ALL_EXCHANGES, EXCHANGE_TRADING_PAIRS, API_KEYS, TRADING_SYMBOL
    )
    detector = ArbitrageDetector(monitor, MIN_PROFIT_PERCENTAGE)

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
                    log_with_timestamp(f"🚨 Found {len(opportunities)} arbitrage opportunities:")
                    for i, opp in enumerate(opportunities[:3], 1):
                        log_with_timestamp(f"{i}. Buy on {opp.buy_exchange} at ${opp.buy_price:.2f}")
                        log_with_timestamp(
                            f"   Sell on {opp.sell_exchange} at ${opp.sell_price:.2f}"
                        )
                        log_with_timestamp(
                            f"   Profit: ${opp.profit_usd:.2f} ({opp.profit_percentage:.2f}%)"
                        )
                        log_with_timestamp(f"   Volume limit: {opp.volume_limit:.4f} BTC")
                        print()

                spread_data = monitor.get_price_spread()
                if spread_data:
                    active_exchanges = monitor.get_active_exchanges()
                    all_exchanges = monitor.exchanges

                    log_with_timestamp(
                        f"Active exchanges ({len(active_exchanges)}/{len(all_exchanges)}): {', '.join(active_exchanges)}"
                    )

                    log_with_timestamp(
                        f"Current spread: ${spread_data['spread']:.2f} ({spread_data['spread_percentage']:.2f}%)"
                    )

                    lowest = spread_data["lowest"]
                    highest = spread_data["highest"]
                    log_with_timestamp(f"Lowest: {lowest['exchange']} - ${lowest['price']:.2f} USD")
                    log_with_timestamp(
                        f"Highest: {highest['exchange']} - ${highest['price']:.2f} USD"
                    )
                else:
                    active_exchanges = monitor.get_active_exchanges()
                    all_exchanges = monitor.exchanges
                    inactive_exchanges = [
                        ex for ex in all_exchanges if ex not in active_exchanges
                    ]

                    log_with_timestamp(
                        f"Active exchanges ({len(active_exchanges)}/{len(all_exchanges)}): {', '.join(active_exchanges)}"
                    )
                    if inactive_exchanges:
                        log_with_timestamp(f"Inactive exchanges: {', '.join(inactive_exchanges)}")
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
