import aiohttp
import pytest
from aioresponses import aioresponses

from src.core.arbitrage_detector import ArbitrageOpportunity
from src.services.telegram_service import TelegramService


class TestTelegramService:
    """Test cases for TelegramService"""

    @pytest.mark.unit
    def test_init_with_credentials(self):
        """Test TelegramService initialization with valid credentials"""
        service = TelegramService("test_token", "123456789")

        assert service.bot_token == "test_token"
        assert service.chat_id == "123456789"
        assert service.base_url == "https://api.telegram.org/bottest_token"
        assert service.enabled is True

    @pytest.mark.unit
    def test_init_without_credentials(self):
        """Test TelegramService initialization without credentials"""
        service = TelegramService()

        assert service.bot_token is None
        assert service.chat_id is None
        assert service.base_url is None
        assert service.enabled is False

    @pytest.mark.unit
    def test_init_partial_credentials(self):
        """Test TelegramService initialization with partial credentials"""
        # Only token, no chat_id
        service1 = TelegramService("test_token", None)
        assert service1.enabled is False

        # Only chat_id, no token
        service2 = TelegramService(None, "123456789")
        assert service2.enabled is False

    @pytest.mark.unit
    async def test_send_message_disabled(self):
        """Test sending message when service is disabled"""
        service = TelegramService()
        result = await service.send_message("test message")

        assert result is False

    @pytest.mark.unit
    async def test_send_message_success(self):
        """Test successful message sending"""
        service = TelegramService("test_token", "123456789")

        with aioresponses() as mock:
            url = "https://api.telegram.org/bottest_token/sendMessage"
            mock.post(
                url, status=200, payload={"ok": True, "result": {"message_id": 123}}
            )

            result = await service.send_message("Test message")

            assert result is True

            # Verify the request was made
            assert len(mock.requests) == 1
            request_info = list(mock.requests.keys())[0]
            assert request_info[0] == "POST"
            assert request_info[1].human_repr() == url

    @pytest.mark.unit
    async def test_send_message_api_error(self):
        """Test message sending with API error response"""
        service = TelegramService("test_token", "123456789")

        with aioresponses() as mock:
            url = "https://api.telegram.org/bottest_token/sendMessage"
            mock.post(
                url,
                status=400,
                payload={"ok": False, "error_code": 400, "description": "Bad Request"},
            )

            result = await service.send_message("Test message")

            assert result is False

    @pytest.mark.unit
    async def test_send_message_network_error(self):
        """Test message sending with network error"""
        service = TelegramService("test_token", "123456789")

        with aioresponses() as mock:
            url = "https://api.telegram.org/bottest_token/sendMessage"
            mock.post(url, exception=aiohttp.ClientError("Network error"))

            result = await service.send_message("Test message")

            assert result is False

    @pytest.mark.unit
    async def test_send_arbitrage_alert_disabled(self):
        """Test sending arbitrage alert when service is disabled"""
        service = TelegramService()

        opportunity = ArbitrageOpportunity(
            buy_exchange="coinmate",
            sell_exchange="kraken",
            buy_price=42000.0,
            sell_price=42100.0,
            profit_usd=100.0,
            profit_percentage=0.24,
            timestamp=1703254800.0,
            volume_limit=1.5,
        )

        result = await service.send_arbitrage_alert(opportunity)
        assert result is False

    @pytest.mark.unit
    async def test_send_arbitrage_alert_success(self):
        """Test successful arbitrage alert sending"""
        service = TelegramService("test_token", "123456789")

        opportunity = ArbitrageOpportunity(
            buy_exchange="coinmate",
            sell_exchange="kraken",
            buy_price=42000.0,
            sell_price=42100.0,
            profit_usd=100.0,
            profit_percentage=0.24,
            timestamp=1703254800.0,
            volume_limit=1.5,
        )

        with aioresponses() as mock:
            url = "https://api.telegram.org/bottest_token/sendMessage"
            mock.post(
                url, status=200, payload={"ok": True, "result": {"message_id": 123}}
            )

            result = await service.send_arbitrage_alert(opportunity)

            assert result is True

            # Verify the request was made
            assert len(mock.requests) == 1

    @pytest.mark.unit
    async def test_send_system_alert_success(self):
        """Test successful system alert sending"""
        service = TelegramService("test_token", "123456789")

        with aioresponses() as mock:
            url = "https://api.telegram.org/bottest_token/sendMessage"
            mock.post(
                url, status=200, payload={"ok": True, "result": {"message_id": 123}}
            )

            result = await service.send_system_alert("System is online")

            assert result is True

            # Verify the request was made
            assert len(mock.requests) == 1

    @pytest.mark.unit
    async def test_test_connection_disabled(self):
        """Test connection test when service is disabled"""
        service = TelegramService()

        result = await service.test_connection()
        assert result is False

    @pytest.mark.unit
    async def test_test_connection_success(self):
        """Test successful connection test"""
        service = TelegramService("test_token", "123456789")

        with aioresponses() as mock:
            url = "https://api.telegram.org/bottest_token/sendMessage"
            mock.post(
                url, status=200, payload={"ok": True, "result": {"message_id": 123}}
            )

            result = await service.test_connection()

            assert result is True

            # Verify the request was made
            assert len(mock.requests) == 1

    @pytest.mark.unit
    async def test_test_connection_failure(self):
        """Test connection test failure"""
        service = TelegramService("test_token", "123456789")

        with aioresponses() as mock:
            url = "https://api.telegram.org/bottest_token/sendMessage"
            mock.post(
                url,
                status=401,
                payload={"ok": False, "error_code": 401, "description": "Unauthorized"},
            )

            result = await service.test_connection()

            assert result is False


class TestTelegramServiceIntegration:
    """Integration tests for TelegramService"""

    @pytest.mark.integration
    async def test_real_telegram_api_call(self):
        """Test real Telegram API call (requires valid credentials in environment)"""
        import os

        from dotenv import load_dotenv

        # Load environment variables from .env file
        load_dotenv()

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not bot_token or not chat_id:
            pytest.skip("Telegram credentials not available")

        service = TelegramService(bot_token, chat_id)

        # Test with a simple message
        result = await service.send_message(
            "🧪 *Test from pytest*\n\nThis is an automated test message."
        )

        # Should succeed if credentials are valid
        assert result is True

    @pytest.mark.slow
    async def test_real_arbitrage_alert(self):
        """Test real arbitrage alert (requires valid credentials)"""
        import os

        from dotenv import load_dotenv

        # Load environment variables from .env file
        load_dotenv()

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not bot_token or not chat_id:
            pytest.skip("Telegram credentials not available")

        service = TelegramService(bot_token, chat_id)

        # Create a mock arbitrage opportunity
        opportunity = ArbitrageOpportunity(
            buy_exchange="coinmate",
            sell_exchange="kraken",
            buy_price=42000.0,
            sell_price=42250.0,
            profit_usd=250.0,
            profit_percentage=0.60,
            timestamp=1703254800.0,
            volume_limit=2.5,
        )

        result = await service.send_arbitrage_alert(opportunity)
        assert result is True


# Test fixtures for mock data
@pytest.fixture
def mock_arbitrage_opportunity():
    """Create a mock arbitrage opportunity for testing"""
    return ArbitrageOpportunity(
        buy_exchange="coinmate",
        sell_exchange="kraken",
        buy_price=42000.0,
        sell_price=42100.0,
        profit_usd=100.0,
        profit_percentage=0.24,
        timestamp=1703254800.0,
        volume_limit=1.5,
    )


@pytest.fixture
def telegram_service():
    """Create a TelegramService instance for testing"""
    return TelegramService("test_token", "123456789")


@pytest.fixture
def disabled_telegram_service():
    """Create a disabled TelegramService instance for testing"""
    return TelegramService()
