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
            
            # Note: aiogram bots cannot listen to their own outgoing messages
            # Outgoing messages are tracked when sent via the web API in send_message method
            
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
            # Get bot and dispatcher from memory, or create them on-demand
            bot = cls.get_bot(bot_id)
            dp = cls.get_dispatcher(bot_id)
            
            if not bot or not dp:
                logger.info(f"Bot {bot_id} not in memory, creating instances on-demand")
                
                # Get bot from database and create instances
                from .models import Bot as BotModel
                from apps.core.encryption import encryption_service
                from asgiref.sync import sync_to_async
                
                try:
                    # Use sync_to_async for database operations
                    bot_obj = await sync_to_async(BotModel.objects.get)(id=bot_id, status='active')
                    token = await sync_to_async(encryption_service.decrypt)(bot_obj.token_enc)
                    
                    # Create bot and dispatcher instances
                    bot = Bot(token=token)
                    dp = Dispatcher()
                    handler = MessageHandler(bot_id)
                    
                    # Register handlers
                    dp.message.register(handler.handle_message)
                    dp.edited_message.register(handler.handle_edited_message)
                    
                    # Store in memory for subsequent requests
                    cls._bots[bot_id] = bot
                    cls._dispatchers[bot_id] = dp
                    cls._handlers[bot_id] = handler
                    
                    logger.info(f"✅ Created bot instances for bot {bot_id}")
                    
                except BotModel.DoesNotExist:
                    logger.error(f"❌ Bot {bot_id} not found in database or not active")
                    return
                except Exception as e:
                    logger.error(f"❌ Failed to create bot instances for bot {bot_id}: {e}")
                    return
            
            # Create update object
            update = Update(**update_data)
            
            # Process update
            await dp.feed_update(bot, update)
            
        except Exception as e:
            logger.error(f"❌ Error processing webhook for bot {bot_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    @classmethod
    async def send_message(cls, bot_id: int, chat_id: int, text: str, **kwargs):
        """Send message via bot"""
        try:
            # Get bot and dispatcher from memory, or create them on-demand
            bot = cls.get_bot(bot_id)
            
            if not bot:
                logger.info(f"Bot {bot_id} not in memory for sending, creating instance on-demand")
                
                # Get bot from database and create instances
                from .models import Bot as BotModel
                from apps.core.encryption import encryption_service
                from asgiref.sync import sync_to_async
                
                try:
                    # Use sync_to_async for database operations
                    bot_obj = await sync_to_async(BotModel.objects.get)(id=bot_id, status='active')
                    token = await sync_to_async(encryption_service.decrypt)(bot_obj.token_enc)
                    
                    # Create bot instance
                    bot = Bot(token=token)
                    
                    # Store in memory for subsequent requests
                    cls._bots[bot_id] = bot
                    
                    logger.info(f"✅ Created bot instance for sending message via bot {bot_id}")
                    
                except BotModel.DoesNotExist:
                    logger.error(f"❌ Bot {bot_id} not found in database or not active")
                    raise ValueError(f"Bot {bot_id} not found or not active")
                except Exception as e:
                    logger.error(f"❌ Failed to create bot instance for bot {bot_id}: {e}")
                    raise
            
            message = await bot.send_message(chat_id=chat_id, text=text, **kwargs)
            
            # Save outgoing message to database
            from apps.chats.models import Chat
            from apps.messages.models import Message
            from apps.bots.models import Bot as BotModel
            from apps.notifications.services import NotificationService
            from asgiref.sync import sync_to_async
            
            try:
                logger.info(f"🔄 Attempting to save outgoing message for bot {bot_id} to chat {chat_id}")
                
                # Get bot object first
                bot_obj = await sync_to_async(BotModel.objects.get)(id=bot_id)
                
                # Try to get existing chat or create it
                def get_or_create_chat():
                    chat_obj, created = Chat.objects.get_or_create(
                        bot=bot_obj,
                        chat_id=chat_id,
                        defaults={
                            'type': 'bot_chat',
                            'title': f'Chat {chat_id}',
                            'chat_type': 'private'
                        }
                    )
                    if created:
                        logger.info(f"📝 Created new chat {chat_id} for bot {bot_id}")
                    return chat_obj
                
                chat_obj = await sync_to_async(get_or_create_chat)()
                
                def create_message():
                    return Message.objects.create(
                        chat=chat_obj,
                        message_id=message.message_id,
                        from_id=bot_obj.bot_id,  # Use bot's Telegram ID
                        text=text,
                        direction='outgoing',
                        payload={'sent_via': 'web_api', 'date': message.date.isoformat()}
                    )
                
                saved_message = await sync_to_async(create_message)()
                logger.info(f"✅ Sent message via bot {bot_id} to chat {chat_id}, saved outgoing message with ID {saved_message.id}")
                
                # Send notification for the outgoing message
                try:
                    await NotificationService.send_message_notification('new_message', chat_obj, saved_message)
                    logger.info(f"📡 Sent notification for outgoing message {saved_message.id}")
                except Exception as notification_error:
                    logger.error(f"❌ Failed to send notification for outgoing message: {notification_error}")
                
            except BotModel.DoesNotExist:
                logger.error(f"❌ Bot {bot_id} not found in database when saving outgoing message")
            except Exception as e:
                logger.error(f"❌ Error saving outgoing message for bot {bot_id} to chat {chat_id}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error sending message via bot {bot_id}: {e}")
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