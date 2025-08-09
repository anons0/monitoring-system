import asyncio
import logging
import hashlib
from typing import Dict, Optional
from django.conf import settings
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiogram_handlers.message_handler import MessageHandler

logger = logging.getLogger('bots')

class AiogramManager:
    """Manager for aiogram bots"""
    
    # Store active bots
    _bots: Dict[int, Bot] = {}
    _dispatchers: Dict[int, Dispatcher] = {}
    _handlers: Dict[int, MessageHandler] = {}
    _polling_tasks: Dict[int, asyncio.Task] = {}
    
    @classmethod
    def start_bot(cls, bot_id: int, token: str) -> bool:
        """Start a bot with webhook"""
        try:
            if bot_id in cls._bots:
                logger.warning(f"Bot {bot_id} is already running")
                return True
            
            # Create bot instance
            bot = Bot(token=token)
            dp = Dispatcher()
            handler = MessageHandler(bot_id)
            
            # Register handlers
            dp.message.register(handler.handle_message)
            dp.edited_message.register(handler.handle_edited_message)
            
            # Store instances
            cls._bots[bot_id] = bot
            cls._dispatchers[bot_id] = dp
            cls._handlers[bot_id] = handler
            
            # Set up webhook
            success = asyncio.run(cls._setup_webhook(bot_id, bot))
            
            if success:
                logger.info(f"Started bot {bot_id} with webhook")
                return True
            else:
                # Clean up if webhook setup failed
                cls._cleanup_bot(bot_id)
                return False
            
        except Exception as e:
            logger.error(f"Failed to start bot {bot_id}: {e}")
            cls._cleanup_bot(bot_id)
            return False
    
    @classmethod
    def stop_bot(cls, bot_id: int) -> bool:
        """Stop a bot"""
        try:
            if bot_id not in cls._bots:
                logger.warning(f"Bot {bot_id} is not running")
                return True
            
            # Remove webhook
            bot = cls._bots[bot_id]
            try:
                asyncio.run(cls._remove_webhook(bot_id, bot))
            except Exception as e:
                logger.warning(f"Error removing webhook for bot {bot_id}: {e}")
            
            # Clean up bot
            cls._cleanup_bot(bot_id)
            
            logger.info(f"✅ Stopped bot {bot_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop bot {bot_id}: {e}")
            return False
    
    @classmethod
    def get_bot(cls, bot_id: int) -> Optional[Bot]:
        """Get bot instance"""
        return cls._bots.get(bot_id)
    
    @classmethod
    def get_dispatcher(cls, bot_id: int) -> Optional[Dispatcher]:
        """Get dispatcher instance"""
        return cls._dispatchers.get(bot_id)
    
    @classmethod
    async def process_webhook(cls, bot_id: int, update_data: dict):
        """Process webhook update"""
        try:
            bot = cls.get_bot(bot_id)
            dp = cls.get_dispatcher(bot_id)
            
            if not bot or not dp:
                logger.error(f"Bot {bot_id} not found or not running")
                return
            
            # Create update object
            update = Update(**update_data)
            
            # Process update
            await dp.feed_update(bot, update)
            
        except Exception as e:
            logger.error(f"Error processing webhook for bot {bot_id}: {e}")
    
    @classmethod
    async def send_message(cls, bot_id: int, chat_id: int, text: str, **kwargs):
        """Send message via bot"""
        try:
            bot = cls.get_bot(bot_id)
            if not bot:
                raise ValueError(f"Bot {bot_id} not found or not running")
            
            message = await bot.send_message(chat_id=chat_id, text=text, **kwargs)
            
            # Save outgoing message to database
            from apps.chats.models import Chat
            from apps.messages.models import Message
            
            try:
                chat_obj = Chat.objects.get(bot_id=bot_id, chat_id=chat_id)
                Message.objects.create(
                    chat=chat_obj,
                    message_id=message.message_id,
                    from_id=bot.id,
                    text=text,
                    direction='outgoing',
                    payload={'sent_via': 'api'}
                )
            except Chat.DoesNotExist:
                logger.warning(f"Chat {chat_id} not found for bot {bot_id}")
            
            return message
            
        except Exception as e:
            logger.error(f"Error sending message via bot {bot_id}: {e}")
            raise
    
    @classmethod
    def get_active_bots(cls) -> list:
        """Get list of active bot IDs"""
        return list(cls._bots.keys())
    
    @classmethod
    async def _setup_webhook(cls, bot_id: int, bot: Bot) -> bool:
        """Set up webhook for bot"""
        try:
            # Generate webhook URL and secret
            webhook_secret = cls._generate_webhook_secret(bot_id)
            webhook_url = cls._get_webhook_url(bot_id, webhook_secret)
            
            # Verify bot connection first
            me = await bot.get_me()
            logger.info(f"🤖 Bot authenticated: @{me.username} ({me.first_name})")
            
            # Remove any existing webhook first
            await bot.delete_webhook()
            logger.info(f"🗑️ Removed existing webhook for bot {bot_id}")
            
            # Set new webhook
            await bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message", "edited_message", "callback_query"],
                drop_pending_updates=False,  # Don't drop pending updates
                secret_token=webhook_secret
            )
            
            logger.info(f"🔗 Set webhook for bot {bot_id}: {webhook_url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up webhook for bot {bot_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Update bot status to error
            try:
                from .models import Bot as BotModel
                from django.db import transaction
                
                with transaction.atomic():
                    bot_obj = BotModel.objects.get(id=bot_id)
                    bot_obj.status = 'error'
                    bot_obj.save()
                    logger.error(f"📝 Updated bot {bot_id} status to error")
            except Exception as db_error:
                logger.error(f"❌ Failed to update bot status: {db_error}")
            
            return False
    
    @classmethod
    async def _remove_webhook(cls, bot_id: int, bot: Bot):
        """Remove webhook for bot"""
        try:
            await bot.delete_webhook()
            logger.info(f"🗑️ Removed webhook for bot {bot_id}")
        except Exception as e:
            logger.error(f"❌ Error removing webhook for bot {bot_id}: {e}")
    
    @classmethod
    def _cleanup_bot(cls, bot_id: int):
        """Clean up bot instances"""
        try:
            # Close bot session
            if bot_id in cls._bots:
                bot = cls._bots[bot_id]
                try:
                    # Try to close session properly
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(bot.session.close())
                    else:
                        asyncio.run(bot.session.close())
                except Exception as e:
                    logger.warning(f"Error closing bot session: {e}")
            
            # Remove from storage
            if bot_id in cls._bots:
                del cls._bots[bot_id]
            if bot_id in cls._dispatchers:
                del cls._dispatchers[bot_id]
            if bot_id in cls._handlers:
                del cls._handlers[bot_id]
            if bot_id in cls._polling_tasks:  # Clean up any remaining polling tasks
                del cls._polling_tasks[bot_id]
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up bot {bot_id}: {e}")
    
    @classmethod
    def _generate_webhook_secret(cls, bot_id: int) -> str:
        """Generate webhook secret for bot"""
        return hashlib.sha256(f"bot_{bot_id}_webhook".encode()).hexdigest()[:32]
    
    @classmethod
    def _get_webhook_url(cls, bot_id: int, secret: str) -> str:
        """Get webhook URL for bot"""
        # Get base URL from settings or use default
        base_url = getattr(settings, 'WEBHOOK_BASE_URL', 'https://your-domain.com')
        return f"{base_url}/webhook/bot/{bot_id}/{secret}/"