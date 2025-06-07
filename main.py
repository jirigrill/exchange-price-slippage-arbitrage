import asyncio
from src.exchange_monitor import ExchangeMonitor
from src.arbitrage_detector import ArbitrageDetector
from config import (
    ALL_EXCHANGES,
    TRADING_SYMBOL,
    MIN_PROFIT_PERCENTAGE,
    EXCHANGE_TRADING_PAIRS,
    API_KEYS,
)


async def main():
    print("Starting Bitcoin Latency Arbitrage POC...")
    print(f"Monitoring exchanges: {ALL_EXCHANGES}")
    print(f"Trading symbol: {TRADING_SYMBOL}")
    print(f"Minimum profit threshold: {MIN_PROFIT_PERCENTAGE}%")
    print("-" * 50)

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
                    print(f"\n🚨 Found {len(opportunities)} arbitrage opportunities:")
                    for i, opp in enumerate(opportunities[:3], 1):
                        print(f"{i}. Buy on {opp.buy_exchange} at ${opp.buy_price:.2f}")
                        print(
                            f"   Sell on {opp.sell_exchange} at ${opp.sell_price:.2f}"
                        )
                        print(
                            f"   Profit: ${opp.profit_usd:.2f} ({opp.profit_percentage:.2f}%)"
                        )
                        print(f"   Volume limit: {opp.volume_limit:.4f} BTC")
                        print()

                spread_data = monitor.get_price_spread()
                if spread_data:
                    active_exchanges = monitor.get_active_exchanges()
                    all_exchanges = monitor.exchanges

                    print(
                        f"Active exchanges ({len(active_exchanges)}/{len(all_exchanges)}): {', '.join(active_exchanges)}"
                    )

                    print(
                        f"Current spread: ${spread_data['spread']:.2f} ({spread_data['spread_percentage']:.2f}%)"
                    )

                    lowest = spread_data["lowest"]
                    highest = spread_data["highest"]
                    print(f"Lowest: {lowest['exchange']} - ${lowest['price']:.2f} USD")
                    print(
                        f"Highest: {highest['exchange']} - ${highest['price']:.2f} USD"
                    )
                else:
                    active_exchanges = monitor.get_active_exchanges()
                    all_exchanges = monitor.exchanges
                    inactive_exchanges = [
                        ex for ex in all_exchanges if ex not in active_exchanges
                    ]

                    print(
                        f"Active exchanges ({len(active_exchanges)}/{len(all_exchanges)}): {', '.join(active_exchanges)}"
                    )
                    if inactive_exchanges:
                        print(f"Inactive exchanges: {', '.join(inactive_exchanges)}")
                    print("No spread data available yet...")

                await asyncio.sleep(5)

            except KeyboardInterrupt:
                print("\nStopping arbitrage monitor...")
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(1)

    await monitor_and_detect()


if __name__ == "__main__":
    asyncio.run(main())
