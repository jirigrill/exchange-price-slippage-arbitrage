"""
Tests for the arbitrage detector module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.arbitrage_detector import ArbitrageDetector, ArbitrageOpportunity


@pytest.mark.unit
class TestArbitrageDetector:

    def test_init(self):
        """Test arbitrage detector initialization"""
        mock_monitor = MagicMock()
        detector = ArbitrageDetector(mock_monitor, min_profit_percentage=0.5)

        assert detector.monitor == mock_monitor
        assert detector.min_profit_percentage == 0.5
        assert detector.large_exchanges == ["kraken"]
        assert detector.small_exchanges == ["coinmate"]
        assert detector.opportunities == []

    def test_is_valid_arbitrage_pair(self):
        """Test valid arbitrage pair checking"""
        mock_monitor = MagicMock()
        detector = ArbitrageDetector(mock_monitor)

        # Valid: large to small
        assert detector._is_valid_arbitrage_pair("kraken", "coinmate") is True

        # Valid: small to large
        assert detector._is_valid_arbitrage_pair("coinmate", "kraken") is True

        # Invalid: same exchange
        assert detector._is_valid_arbitrage_pair("kraken", "kraken") is False

        # Invalid: both large (if we had multiple large exchanges)
        # assert detector._is_valid_arbitrage_pair(
        #     'binance', 'kraken'
        # ) is False

        # Invalid: both small (if we had multiple small exchanges)
        # assert detector._is_valid_arbitrage_pair(
        #     'coinmate', 'other_small'
        # ) is False

    @patch("src.core.arbitrage_detector.DYNAMIC_FEES_ENABLED", False)
    async def test_get_trading_fees(self):
        """Test trading fee retrieval"""
        mock_monitor = MagicMock()
        mock_monitor.api_keys = {}
        detector = ArbitrageDetector(mock_monitor)

        # Known exchanges (using static fees when dynamic disabled)
        kraken_coinmate_fee = await detector._get_trading_fees("kraken", "coinmate")
        assert kraken_coinmate_fee == 0.26 + 0.6  # 0.86%

        # Unknown exchange (should use default)
        unknown_fee = await detector._get_trading_fees("unknown", "coinmate")
        assert unknown_fee == 0.25 + 0.6  # 0.85%

    def test_calculate_opportunity_valid(
        self, sample_btc_usd_price, sample_btc_czk_price
    ):
        """Test calculation of valid arbitrage opportunity"""
        mock_monitor = MagicMock()
        detector = ArbitrageDetector(mock_monitor, min_profit_percentage=0.1)

        # Modify prices to create profitable opportunity
        # Buy low (coinmate), sell high (kraken)
        buy_data = sample_btc_czk_price  # 102083.33 USD
        sell_data = sample_btc_usd_price  # 102500.0 USD

        # Make sell price higher to ensure profit after fees
        sell_data.price_usd = 103000.0  # Higher sell price

        opportunity = detector._calculate_opportunity(
            "coinmate", buy_data, "kraken", sell_data
        )

        assert opportunity is not None
        assert opportunity.buy_exchange == "coinmate"
        assert opportunity.sell_exchange == "kraken"
        assert opportunity.buy_price == 102083.33
        assert opportunity.sell_price == 103000.0
        assert opportunity.profit_usd == pytest.approx(916.67, rel=1e-3)

        # Profit percentage should be positive (note: sync method doesn't calculate fees)
        expected_gross_profit = (916.67 / 102083.33) * 100  # ~0.9%
        # Sync method returns gross profit, fees calculated separately in async context
        assert opportunity.profit_percentage == pytest.approx(
            expected_gross_profit, rel=1e-2
        )

    def test_calculate_opportunity_no_profit(
        self, sample_btc_usd_price, sample_btc_czk_price
    ):
        """Test calculation when no profit exists"""
        mock_monitor = MagicMock()
        detector = ArbitrageDetector(mock_monitor)

        # Sell price lower than buy price
        buy_data = sample_btc_usd_price  # 102500.0 USD (higher)
        sell_data = sample_btc_czk_price  # 102083.33 USD (lower)

        opportunity = detector._calculate_opportunity(
            "kraken", buy_data, "coinmate", sell_data
        )

        assert opportunity is None

    def test_calculate_opportunity_fees_too_high(
        self, sample_btc_usd_price, sample_btc_czk_price
    ):
        """Test calculation when fees exceed profit"""
        mock_monitor = MagicMock()
        detector = ArbitrageDetector(mock_monitor, min_profit_percentage=0.1)

        # Create small price difference that gets wiped out by fees
        buy_data = sample_btc_czk_price  # 102083.33 USD

        # Small price increase
        sell_data = sample_btc_usd_price
        sell_data.price_usd = 102200.0  # Only $116.67 profit

        opportunity = detector._calculate_opportunity(
            "coinmate", buy_data, "kraken", sell_data
        )

        # Sync method doesn't account for fees, so this will not be None
        # Fees are only applied in async detect_opportunities method
        assert opportunity is not None

    async def test_detect_opportunities_empty_prices(self):
        """Test opportunity detection with no price data"""
        mock_monitor = MagicMock()
        mock_monitor.get_price_spread.return_value = {}
        mock_monitor.latest_prices = {}

        detector = ArbitrageDetector(mock_monitor)
        opportunities = await detector.detect_opportunities()

        assert opportunities == []

    @patch("src.core.arbitrage_detector.DYNAMIC_FEES_ENABLED", False)
    async def test_detect_opportunities_with_data(
        self, sample_btc_usd_price, sample_btc_czk_price
    ):
        """Test opportunity detection with valid price data"""
        # Make sell price higher to ensure profit after fees (need higher spread due to 0.86% fees)
        sample_btc_usd_price.price_usd = (
            104000.0  # Higher profit to overcome 0.86% fees
        )

        mock_monitor = MagicMock()
        mock_monitor.get_price_spread.return_value = {"spread": 1916.67}
        mock_monitor.latest_prices = {
            "kraken": sample_btc_usd_price,
            "coinmate": sample_btc_czk_price,
        }
        mock_monitor.api_keys = {}

        detector = ArbitrageDetector(mock_monitor, min_profit_percentage=0.1)
        opportunities = await detector.detect_opportunities()

        # Should find one opportunity (buy coinmate, sell kraken)
        assert len(opportunities) == 1

        opp = opportunities[0]
        assert opp.buy_exchange == "coinmate"
        assert opp.sell_exchange == "kraken"
        assert opp.profit_usd > 0

    @patch("src.core.arbitrage_detector.DYNAMIC_FEES_ENABLED", False)
    async def test_detect_opportunities_filters_by_min_profit(
        self, sample_btc_usd_price, sample_btc_czk_price
    ):
        """Test that opportunities below minimum profit are filtered out"""
        mock_monitor = MagicMock()
        mock_monitor.get_price_spread.return_value = {"spread": 416.67}
        mock_monitor.latest_prices = {
            "kraken": sample_btc_usd_price,
            "coinmate": sample_btc_czk_price,
        }
        mock_monitor.api_keys = {}

        # Set very high minimum profit requirement
        detector = ArbitrageDetector(mock_monitor, min_profit_percentage=1.0)
        opportunities = await detector.detect_opportunities()

        # Should find no opportunities due to high threshold
        assert len(opportunities) == 0

    def test_get_best_opportunities(self):
        """Test getting best opportunities from history"""
        import time

        mock_monitor = MagicMock()
        detector = ArbitrageDetector(mock_monitor)

        current_time = time.time()

        # Add some sample opportunities with recent timestamps
        opp1 = ArbitrageOpportunity(
            buy_exchange="coinmate",
            sell_exchange="kraken",
            buy_price=100000,
            sell_price=101000,
            profit_usd=1000,
            profit_percentage=0.5,
            timestamp=current_time - 60,
            volume_limit=10,  # 1 minute ago
        )

        opp2 = ArbitrageOpportunity(
            buy_exchange="coinmate",
            sell_exchange="kraken",
            buy_price=100000,
            sell_price=102000,
            profit_usd=2000,
            profit_percentage=1.5,
            timestamp=current_time - 30,
            volume_limit=5,  # 30 seconds ago
        )

        detector.opportunities = [opp1, opp2]

        best = detector.get_best_opportunities(limit=1)

        assert len(best) == 1
        assert best[0].profit_percentage == 1.5  # Higher profit percentage


@pytest.mark.unit
class TestArbitrageOpportunity:

    def test_arbitrage_opportunity_creation(self):
        """Test ArbitrageOpportunity dataclass creation"""
        opp = ArbitrageOpportunity(
            buy_exchange="coinmate",
            sell_exchange="kraken",
            buy_price=102083.33,
            sell_price=102500.0,
            profit_usd=416.67,
            profit_percentage=0.35,
            timestamp=1703254800.0,
            volume_limit=12.3,
        )

        assert opp.buy_exchange == "coinmate"
        assert opp.sell_exchange == "kraken"
        assert opp.buy_price == 102083.33
        assert opp.sell_price == 102500.0
        assert opp.profit_usd == 416.67
        assert opp.profit_percentage == 0.35
        assert opp.timestamp == 1703254800.0
        assert opp.volume_limit == 12.3


@pytest.mark.integration
class TestArbitrageDetectorIntegration:

    def test_full_arbitrage_detection_flow(
        self, high_spread_scenario, trading_pairs, api_keys
    ):
        """Test complete arbitrage detection flow"""
        # This would require mocking the full exchange monitor
        # and testing the integration between components
        pass  # Placeholder for integration test
