import asyncio
import logging
from typing import Dict, Optional
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
        """Start a bot"""
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
            
            # Start polling for updates
            cls._start_polling(bot_id, bot, dp)
            
            logger.info(f"Started bot {bot_id} with polling")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start bot {bot_id}: {e}")
            return False
    
    @classmethod
    def stop_bot(cls, bot_id: int) -> bool:
        """Stop a bot"""
        try:
            if bot_id not in cls._bots:
                logger.warning(f"Bot {bot_id} is not running")
                return True
            
            # Stop polling task
            if bot_id in cls._polling_tasks:
                task_or_thread = cls._polling_tasks[bot_id]
                logger.info(f"🛑 Stopping polling for bot {bot_id}")
                
                if hasattr(task_or_thread, 'cancel'):
                    # It's an asyncio task
                    task_or_thread.cancel()
                    logger.info(f"Cancelled polling task for bot {bot_id}")
                elif hasattr(task_or_thread, 'join'):
                    # It's a thread - signal it to stop
                    logger.info(f"Signaled polling thread to stop for bot {bot_id}")
                
                del cls._polling_tasks[bot_id]
            
            # Close bot session
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
            del cls._bots[bot_id]
            del cls._dispatchers[bot_id]
            del cls._handlers[bot_id]
            
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
    def _start_polling(cls, bot_id: int, bot: Bot, dp: Dispatcher):
        """Start polling for bot updates"""
        try:
            # Create asyncio task instead of threading
            def create_task():
                # Check if we have an event loop running
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No loop running, create one in a new thread
                    import threading
                    
                    def polling_worker():
                        """Worker function for polling in a separate thread"""
                        logger.info(f"🔄 Starting polling worker for bot {bot_id}")
                        
                        # Set up asyncio event loop for this thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            # Create and run the polling task
                            task = loop.create_task(cls._polling_loop(bot_id, bot, dp))
                            cls._polling_tasks[bot_id] = task  # Store task reference
                            loop.run_until_complete(task)
                        except Exception as e:
                            logger.error(f"❌ Polling worker error for bot {bot_id}: {e}")
                        finally:
                            loop.close()
                    
                    # Start polling in daemon thread
                    polling_thread = threading.Thread(target=polling_worker, daemon=True)
                    polling_thread.start()
                    return polling_thread
                else:
                    # We have a running loop, create task directly
                    task = loop.create_task(cls._polling_loop(bot_id, bot, dp))
                    cls._polling_tasks[bot_id] = task
                    return task
            
            # Start polling
            polling_ref = create_task()
            
            logger.info(f"✅ Started polling for bot {bot_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to start polling for bot {bot_id}: {e}")
    
    @classmethod
    async def _polling_loop(cls, bot_id: int, bot: Bot, dp: Dispatcher):
        """Main polling loop"""
        logger.info(f"🚀 Starting polling loop for bot {bot_id}")
        
        try:
            # Verify bot connection first
            me = await bot.get_me()
            logger.info(f"🤖 Bot authenticated: @{me.username} ({me.first_name})")
            
            # Start polling with proper error handling
            logger.info(f"📡 Starting message polling for bot {bot_id}...")
            await dp.start_polling(
                bot,
                skip_updates=False,  # Don't skip updates - we want all messages!
                allowed_updates=["message", "edited_message", "callback_query"],
                close_bot_session=False  # Keep session alive
            )
            
        except asyncio.CancelledError:
            logger.info(f"⏹️ Polling cancelled for bot {bot_id}")
            raise  # Re-raise to properly handle cancellation
        except Exception as e:
            logger.error(f"❌ Error in polling loop for bot {bot_id}: {e}")
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
            
            # Re-raise the original exception
            raise