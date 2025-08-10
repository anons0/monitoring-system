import logging
import os
import sys

# Add backend directory to Python path if not already in path
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.append(backend_path)

# Django setup is handled by the main application
# Don't call django.setup() here to avoid circular imports

from aiogram import types
from aiogram.filters import Command

logger = logging.getLogger('bots')

class MessageHandler:
    """Handler for bot messages"""
    
    def __init__(self, bot_id: int):
        self.bot_id = bot_id
    
    async def handle_message(self, message: types.Message):
        """Handle incoming message"""
        try:
            logger.info(f"🔔 INCOMING MESSAGE!")
            logger.info(f"   From: {message.from_user.username or message.from_user.first_name or f'User {message.from_user.id}'}")
            logger.info(f"   Chat: {message.chat.id} ({message.chat.type})")
            logger.info(f"   Text: {message.text[:100] if message.text else '[No text]'}")
            logger.info(f"   Bot ID: {self.bot_id}")
            
            # Import Django models here to avoid circular imports
            from apps.chats.models import Chat
            from apps.messages.models import Message
            from apps.core.models import TelegramUser
            from apps.bots.models import Bot
            from apps.notifications.services import NotificationService
            
            # Import Django models here to avoid circular imports
            from django.db import transaction
            
            # Import sync_to_async for database operations
            from asgiref.sync import sync_to_async
            
            # Get or create bot
            bot = await sync_to_async(self._get_bot_sync)()
            if not bot:
                return
            
            # Get or create chat
            chat = await sync_to_async(self._get_or_create_chat_sync)(bot, message.chat)
            
            # Get or create user
            user = await sync_to_async(self._get_or_create_user_sync)(message.from_user)
            
            # Save message
            saved_message = await sync_to_async(self._save_message_sync)(chat, message, 'incoming')
            
            logger.info(f"✅ Successfully saved message from {user.username or user.first_name} in chat {chat.title or chat.chat_id}")
            logger.info(f"📝 Message saved with ID: {saved_message.id}")
            
            # Handle auto-reply for non-command messages
            await self._handle_auto_reply(bot, message, chat)
            
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def handle_edited_message(self, edited_message: types.Message):
        """Handle edited message"""
        try:
            # Import Django models here to avoid circular imports
            from apps.chats.models import Chat
            from apps.messages.models import Message
            from apps.bots.models import Bot
            from apps.notifications.services import NotificationService
            
            # Find existing message and update it
            bot = await self._get_bot()
            if not bot:
                return
            
            chat = Chat.objects.filter(bot=bot, chat_id=edited_message.chat.id).first()
            if chat:
                message = Message.objects.filter(
                    chat=chat,
                    message_id=edited_message.message_id
                ).first()
                
                if message:
                    message.text = edited_message.text or edited_message.caption
                    message.payload.update({
                        'edited': True,
                        'edit_date': edited_message.edit_date.isoformat() if edited_message.edit_date else None
                    })
                    message.save()
                    
                    # Send notification
                    await NotificationService.send_message_notification(
                        'message_edited', chat, message
                    )
            
        except Exception as e:
            logger.error(f"Error handling edited message: {e}")
    
    async def _get_bot(self):
        """Get bot instance"""
        try:
            from apps.bots.models import Bot
            return Bot.objects.get(id=self.bot_id)
        except Exception as e:  # Catch both Bot.DoesNotExist and import errors
            logger.error(f"Bot {self.bot_id} not found: {e}")
            return None
    
    def _get_bot_sync(self):
        """Get bot instance synchronously"""
        try:
            from apps.bots.models import Bot
            return Bot.objects.get(id=self.bot_id)
        except Exception as e:  # Catch both Bot.DoesNotExist and import errors
            logger.error(f"Bot {self.bot_id} not found: {e}")
            return None
    
    async def _get_or_create_chat(self, bot, tg_chat: types.Chat):
        """Get or create chat"""
        from apps.chats.models import Chat
        
        chat, created = Chat.objects.get_or_create(
            bot=bot,
            chat_id=tg_chat.id,
            defaults={
                'type': 'bot_chat',
                'title': tg_chat.title or f"{tg_chat.first_name or ''} {tg_chat.last_name or ''}".strip(),
                'chat_type': tg_chat.type,
            }
        )
        
        if created:
            logger.info(f"Created new chat: {chat.title or chat.chat_id}")
        
        return chat
    
    def _get_or_create_chat_sync(self, bot, tg_chat: types.Chat):
        """Get or create chat synchronously"""
        from apps.chats.models import Chat
        
        chat, created = Chat.objects.get_or_create(
            bot=bot,
            chat_id=tg_chat.id,
            defaults={
                'type': 'bot_chat',
                'title': tg_chat.title or f"{tg_chat.first_name or ''} {tg_chat.last_name or ''}".strip(),
                'chat_type': tg_chat.type,
            }
        )
        
        if created:
            logger.info(f"Created new chat: {chat.title or chat.chat_id}")
        
        return chat
    
    async def _get_or_create_user(self, tg_user: types.User):
        """Get or create user"""
        from apps.core.models import TelegramUser
        
        user, created = TelegramUser.objects.get_or_create(
            telegram_user_id=tg_user.id,
            type='bot_user',
            defaults={
                'username': tg_user.username,
                'first_name': tg_user.first_name,
                'last_name': tg_user.last_name,
            }
        )
        
        if not created:
            # Update user info if changed
            if (user.username != tg_user.username or 
                user.first_name != tg_user.first_name or 
                user.last_name != tg_user.last_name):
                user.username = tg_user.username
                user.first_name = tg_user.first_name
                user.last_name = tg_user.last_name
                user.save()
        
        return user
    
    def _get_or_create_user_sync(self, tg_user: types.User):
        """Get or create user synchronously"""
        from apps.core.models import TelegramUser
        
        user, created = TelegramUser.objects.get_or_create(
            telegram_user_id=tg_user.id,
            type='bot_user',
            defaults={
                'username': tg_user.username,
                'first_name': tg_user.first_name,
                'last_name': tg_user.last_name,
            }
        )
        
        if not created:
            # Update user info if changed
            if (user.username != tg_user.username or 
                user.first_name != tg_user.first_name or 
                user.last_name != tg_user.last_name):
                user.username = tg_user.username
                user.first_name = tg_user.first_name
                user.last_name = tg_user.last_name
                user.save()
        
        return user
    
    async def _save_message(self, chat, tg_message: types.Message, direction: str):
        """Save message to database"""
        from apps.messages.models import Message
        from apps.notifications.services import NotificationService
        
        # Determine media type
        media_type = None
        media_file_id = None
        
        if tg_message.photo:
            media_type = 'photo'
            media_file_id = tg_message.photo[-1].file_id
        elif tg_message.video:
            media_type = 'video'
            media_file_id = tg_message.video.file_id
        elif tg_message.document:
            media_type = 'document'
            media_file_id = tg_message.document.file_id
        elif tg_message.voice:
            media_type = 'voice'
            media_file_id = tg_message.voice.file_id
        elif tg_message.audio:
            media_type = 'audio'
            media_file_id = tg_message.audio.file_id
        elif tg_message.sticker:
            media_type = 'sticker'
            media_file_id = tg_message.sticker.file_id
        
        # Create message
        message = Message.objects.create(
            chat=chat,
            message_id=tg_message.message_id,
            from_id=tg_message.from_user.id,
            text=tg_message.text or tg_message.caption,
            direction=direction,
            reply_to_message_id=tg_message.reply_to_message.message_id if tg_message.reply_to_message else None,
            media_type=media_type,
            media_file_id=media_file_id,
            payload={
                'message_type': tg_message.content_type,
                'date': tg_message.date.isoformat(),
                'entities': [entity.model_dump() for entity in (tg_message.entities or [])],
            }
        )
        
        # Send notification
        await NotificationService.send_message_notification('new_message', chat, message)
    
    def _save_message_sync(self, chat, tg_message: types.Message, direction: str):
        """Save message to database synchronously"""
        from apps.messages.models import Message
        from apps.notifications.services import NotificationService
        
        # Determine media type
        media_type = None
        media_file_id = None
        
        if tg_message.photo:
            media_type = 'photo'
            media_file_id = tg_message.photo[-1].file_id
        elif tg_message.video:
            media_type = 'video'
            media_file_id = tg_message.video.file_id
        elif tg_message.document:
            media_type = 'document'
            media_file_id = tg_message.document.file_id
        elif tg_message.voice:
            media_type = 'voice'
            media_file_id = tg_message.voice.file_id
        elif tg_message.audio:
            media_type = 'audio'
            media_file_id = tg_message.audio.file_id
        elif tg_message.sticker:
            media_type = 'sticker'
            media_file_id = tg_message.sticker.file_id
        
        # Create message
        message = Message.objects.create(
            chat=chat,
            message_id=tg_message.message_id,
            from_id=tg_message.from_user.id,
            text=tg_message.text or tg_message.caption,
            direction=direction,
            reply_to_message_id=tg_message.reply_to_message.message_id if tg_message.reply_to_message else None,
            media_type=media_type,
            media_file_id=media_file_id,
            payload={
                'message_type': tg_message.content_type,
                'date': tg_message.date.isoformat(),
                'entities': [entity.model_dump() for entity in (tg_message.entities or [])],
            }
        )
        
        # Send notification synchronously
        try:
            NotificationService.send_message_notification_sync('new_message', chat, message)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
        
        return message
    
    async def _handle_auto_reply(self, bot, message: types.Message, chat):
        """Handle auto-reply for non-command messages"""
        try:
            # Skip if message is empty or None
            if not message.text:
                return
            
            # Skip if message is a command (starts with /)
            if message.text.startswith('/'):
                logger.info(f"Skipping auto-reply for command: {message.text}")
                return
            
            # Check if bot has auto-reply enabled
            if not bot.auto_reply_enabled or not bot.auto_reply_message:
                logger.info(f"Auto-reply disabled for bot {bot.id}")
                return
            
            # Send auto-reply message
            from aiogram import Bot as AiogramBot
            from apps.core.encryption import encryption_service
            from asgiref.sync import sync_to_async
            
            try:
                # Get bot token
                token = await sync_to_async(encryption_service.decrypt)(bot.token_enc)
                aiogram_bot = AiogramBot(token=token)
                
                # Send auto-reply
                await aiogram_bot.send_message(
                    chat_id=message.chat.id,
                    text=bot.auto_reply_message,
                    parse_mode='HTML'
                )
                
                # Close bot session
                await aiogram_bot.session.close()
                
                logger.info(f"✅ Sent auto-reply to chat {message.chat.id} from bot {bot.id}")
                
                # Save auto-reply as outgoing message
                from apps.messages.models import Message
                try:
                    def create_auto_reply_message():
                        return Message.objects.create(
                            chat=chat,
                            message_id=0,  # We don't have message_id for auto-reply
                            from_id=bot.bot_id,
                            text=bot.auto_reply_message,
                            direction='outgoing',
                            payload={'auto_reply': True, 'sent_via': 'auto_reply'}
                        )
                    
                    await sync_to_async(create_auto_reply_message)()
                    logger.info(f"💾 Saved auto-reply message to database")
                    
                except Exception as save_error:
                    logger.error(f"❌ Failed to save auto-reply message: {save_error}")
                
            except Exception as send_error:
                logger.error(f"❌ Failed to send auto-reply: {send_error}")
            
        except Exception as e:
            logger.error(f"❌ Error in auto-reply handler: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")