from django.test import TestCase
from apps.bots.models import Bot
from apps.accounts.models import Account
from apps.chats.models import Chat
from apps.messages.models import Message
from apps.core.models import TelegramUser
from apps.core.encryption import encryption_service


class ModelTestCase(TestCase):
    """Test model creation and relationships"""

    def test_bot_creation(self):
        """Test creating a bot"""
        token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        encrypted_token = encryption_service.encrypt(token)
        
        bot = Bot.objects.create(
            bot_id=123456789,
            username="test_bot",
            token_enc=encrypted_token,
            status="active"
        )
        
        self.assertEqual(bot.username, "test_bot")
        self.assertEqual(bot.bot_id, 123456789)
        self.assertEqual(bot.status, "active")
        self.assertEqual(encryption_service.decrypt(bot.token_enc), token)

    def test_account_creation(self):
        """Test creating an account"""
        api_id = "12345"
        api_hash = "abcdef123456789"
        
        account = Account.objects.create(
            tg_user_id=987654321,
            phone_number="+1234567890",
            api_id_enc=encryption_service.encrypt(api_id),
            api_hash_enc=encryption_service.encrypt(api_hash),
            status="active"
        )
        
        self.assertEqual(account.phone_number, "+1234567890")
        self.assertEqual(account.tg_user_id, 987654321)
        self.assertEqual(encryption_service.decrypt(account.api_id_enc), api_id)
        self.assertEqual(encryption_service.decrypt(account.api_hash_enc), api_hash)

    def test_telegram_user_creation(self):
        """Test creating a telegram user"""
        user = TelegramUser.objects.create(
            telegram_user_id=111222333,
            username="test_user",
            first_name="Test",
            last_name="User",
            type="bot_user"
        )
        
        self.assertEqual(user.username, "test_user")
        self.assertEqual(user.telegram_user_id, 111222333)
        self.assertEqual(user.type, "bot_user")

    def test_bot_chat_creation(self):
        """Test creating a bot chat"""
        # Create bot first
        bot = Bot.objects.create(
            bot_id=123456789,
            username="test_bot",
            token_enc=encryption_service.encrypt("token"),
            status="active"
        )
        
        chat = Chat.objects.create(
            type="bot_chat",
            bot=bot,
            chat_id=-123456789,
            title="Test Group",
            chat_type="group"
        )
        
        self.assertEqual(chat.type, "bot_chat")
        self.assertEqual(chat.bot, bot)
        self.assertEqual(chat.title, "Test Group")

    def test_message_creation(self):
        """Test creating a message"""
        # Create bot and chat
        bot = Bot.objects.create(
            bot_id=123456789,
            username="test_bot",
            token_enc=encryption_service.encrypt("token"),
            status="active"
        )
        
        chat = Chat.objects.create(
            type="bot_chat",
            bot=bot,
            chat_id=-123456789,
            title="Test Group"
        )
        
        message = Message.objects.create(
            chat=chat,
            message_id=1,
            from_id=111222333,
            text="Hello, world!",
            direction="incoming"
        )
        
        self.assertEqual(message.chat, chat)
        self.assertEqual(message.text, "Hello, world!")
        self.assertEqual(message.direction, "incoming")