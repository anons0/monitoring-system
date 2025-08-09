import asyncio
import logging
from typing import Optional
from django.utils import timezone
from aiogram import Bot as AiogramBot
from aiogram.exceptions import TelegramUnauthorizedError, TelegramBadRequest
from .models import Bot
from apps.core.encryption import encryption_service
from .aiogram_manager import AiogramManager

logger = logging.getLogger('bots')

class BotService:
    """Service for managing bots"""
    
    @staticmethod
    def add_bot(token: str) -> Bot:
        """Add a new bot"""
        try:
            # Basic token format validation
            if not token or ':' not in token:
                raise ValueError("Invalid bot token format. Token should be like '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'")
            
            # Extract bot_id from token
            try:
                bot_id_str = token.split(':')[0]
                bot_id = int(bot_id_str)
            except (ValueError, IndexError):
                raise ValueError("Invalid bot token format")
            
            # Check if bot already exists
            if Bot.objects.filter(bot_id=bot_id).exists():
                raise ValueError(f"Bot with ID {bot_id} already exists")
            
            # Try to get bot info (with better error handling)
            try:
                bot_info = asyncio.run(BotService._get_bot_info(token))
            except Exception as api_error:
                logger.error(f"Failed to validate bot token with Telegram API: {api_error}")
                # For development, create bot with basic info if API fails
                bot_info = {
                    'id': bot_id,
                    'username': f'bot_{bot_id}',
                    'first_name': 'Unknown Bot'
                }
                logger.warning(f"Created bot with fallback info due to API error: {api_error}")
            
            # Encrypt token and save
            try:
                encrypted_token = encryption_service.encrypt(token)
            except Exception as enc_error:
                logger.error(f"Encryption failed: {enc_error}")
                raise ValueError(f"Failed to encrypt bot token: {enc_error}")
            
            bot = Bot.objects.create(
                bot_id=bot_info['id'],
                username=bot_info['username'],
                token_enc=encrypted_token,
                status='inactive'
            )
            
            logger.info(f"Added bot @{bot.username} (ID: {bot.bot_id})")
            return bot
            
        except Exception as e:
            logger.error(f"Failed to add bot: {e}")
            raise
    
    @staticmethod
    async def _get_bot_info(token: str) -> dict:
        """Get bot information from Telegram"""
        try:
            bot = AiogramBot(token=token)
            me = await bot.get_me()
            await bot.session.close()
            
            return {
                'id': me.id,
                'username': me.username,
                'first_name': me.first_name,
            }
        except Exception as e:
            logger.error(f"Failed to get bot info: {e}")
            raise
    
    @staticmethod
    def start_bot(bot: Bot) -> bool:
        """Start a bot"""
        try:
            logger.info(f"Attempting to start bot {bot.id} (@{bot.username})")
            
            # Decrypt token
            try:
                token = encryption_service.decrypt(bot.token_enc)
                logger.info(f"Successfully decrypted token for bot {bot.id}")
            except Exception as e:
                logger.error(f"Failed to decrypt token for bot {bot.id}: {e}")
                bot.status = 'error'
                bot.save()
                return False
            
            # Test token first
            test_result = asyncio.run(BotService._test_bot_async(token))
            if not test_result:
                logger.error(f"Bot token test failed for bot {bot.id}")
                bot.status = 'error'
                bot.save()
                return False
            
            # Start bot
            success = AiogramManager.start_bot(bot.id, token)
            
            if success:
                bot.status = 'active'
                bot.last_seen = timezone.now()
                bot.save()
                logger.info(f"Successfully started bot @{bot.username}")
                return True
            else:
                logger.error(f"AiogramManager failed to start bot {bot.id}")
                bot.status = 'error'
                bot.save()
                return False
                
        except Exception as e:
            logger.error(f"Failed to start bot {bot.id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            bot.status = 'error'
            bot.save()
            return False
    
    @staticmethod
    def stop_bot(bot: Bot) -> bool:
        """Stop a bot"""
        try:
            success = AiogramManager.stop_bot(bot.id)
            
            if success:
                bot.status = 'inactive'
                bot.save()
                logger.info(f"Stopped bot @{bot.username}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to stop bot {bot.id}: {e}")
            return False
    
    @staticmethod
    def test_bot(bot: Bot) -> bool:
        """Test bot connection"""
        try:
            token = encryption_service.decrypt(bot.token_enc)
            result = asyncio.run(BotService._test_bot_async(token))
            return result
        except Exception as e:
            logger.error(f"Failed to test bot {bot.id}: {e}")
            return False
    
    @staticmethod
    async def _test_bot_async(token: str) -> bool:
        """Test bot connection asynchronously"""
        try:
            bot = AiogramBot(token=token)
            await bot.get_me()
            await bot.session.close()
            return True
        except Exception:
            return False