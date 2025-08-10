import logging
from telethon import events
from telethon.tl.types import (
    MessageService, User, Chat, Channel,
    PeerUser, PeerChat, PeerChannel
)
from apps.chats.models import Chat as ChatModel
from apps.messages.models import Message
from apps.core.models import TelegramUser
from apps.accounts.models import Account
from apps.notifications.services import NotificationService

logger = logging.getLogger('accounts')

class EventHandler:
    """Handler for Telethon events"""
    
    def __init__(self, account_id: int):
        self.account_id = account_id
    
    async def handle_new_message(self, event):
        """Handle new incoming message event"""
        try:
            logger.info(f"🔔 INCOMING ACCOUNT MESSAGE!")
            message = event.message
            if isinstance(message, MessageService):
                # Skip service messages for now
                logger.debug(f"Skipping service message from account {self.account_id}")
                return
            
            logger.info(f"   Account ID: {self.account_id}")
            logger.info(f"   Message ID: {message.id}")
            logger.info(f"   Chat: {message.peer_id}")
            logger.info(f"   Text: {(message.text or '')[:100] if message.text else '[No text]'}")
            
            account = await self._get_account()
            if not account:
                logger.error(f"Account {self.account_id} not found in database")
                return
            
            # Get chat information
            chat = await self._get_or_create_chat(account, event.chat, message.peer_id)
            
            # Get sender information
            sender = await self._get_or_create_user(message.from_id, event.sender)
            
            # Save message
            saved_message = await self._save_message(chat, message, 'incoming')
            
            logger.info(f"✅ Successfully saved account message from {sender.username or sender.first_name if sender else 'Unknown'} in chat {chat.title or chat.chat_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling new message for account {self.account_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def handle_outgoing_message(self, event):
        """Handle new outgoing message event"""
        try:
            logger.info(f"📤 OUTGOING ACCOUNT MESSAGE!")
            message = event.message
            if isinstance(message, MessageService):
                # Skip service messages for now
                logger.debug(f"Skipping service message from account {self.account_id}")
                return
            
            logger.info(f"   Account ID: {self.account_id}")
            logger.info(f"   Message ID: {message.id}")
            logger.info(f"   Chat: {message.peer_id}")
            logger.info(f"   Text: {(message.text or '')[:100] if message.text else '[No text]'}")
            
            account = await self._get_account()
            if not account:
                logger.error(f"Account {self.account_id} not found in database")
                return
            
            # Get chat information
            chat = await self._get_or_create_chat(account, event.chat, message.peer_id)
            
            # Save outgoing message
            saved_message = await self._save_message(chat, message, 'outgoing')
            
            logger.info(f"✅ Successfully saved outgoing account message in chat {chat.title or chat.chat_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling outgoing message for account {self.account_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def handle_message_edited(self, event):
        """Handle message edit event"""
        try:
            message = event.message
            account = await self._get_account()
            if not account:
                return
            
            # Find existing message and update it
            chat = await ChatModel.objects.aget(account=account, chat_id=message.peer_id.to_dict()['chat_id'])
            existing_message = await Message.objects.aget(chat=chat, message_id=message.id)
            
            existing_message.text = message.text
            existing_message.payload.update({
                'edited': True,
                'edit_date': message.edit_date.isoformat() if message.edit_date else None
            })
            await existing_message.asave()
            
            # Send notification
            await NotificationService.send_message_notification(
                'message_edited', chat, existing_message
            )
            
        except (ChatModel.DoesNotExist, Message.DoesNotExist):
            logger.warning(f"Could not find existing message to edit for account {self.account_id}")
        except Exception as e:
            logger.error(f"Error handling message edit: {e}")
    
    async def handle_message_deleted(self, event):
        """Handle message deletion event"""
        try:
            account = await self._get_account()
            if not account:
                return
            
            # Mark messages as deleted
            for message_id in event.deleted_ids:
                try:
                    message = await Message.objects.aget(
                        chat__account=account,
                        message_id=message_id
                    )
                    message.payload.update({'deleted': True})
                    await message.asave()
                    
                    await NotificationService.send_message_notification(
                        'message_deleted', message.chat, message
                    )
                    
                except Message.DoesNotExist:
                    continue
                    
        except Exception as e:
            logger.error(f"Error handling message deletion: {e}")
    
    async def _get_account(self) -> Account:
        """Get account instance"""
        try:
            return await Account.objects.aget(id=self.account_id)
        except Account.DoesNotExist:
            logger.error(f"Account {self.account_id} not found")
            return None
    
    async def _get_or_create_chat(self, account: Account, chat_entity, peer_id) -> ChatModel:
        """Get or create chat"""
        # Extract chat ID from peer
        if hasattr(peer_id, 'user_id'):
            chat_id = peer_id.user_id
            chat_type = 'private'
        elif hasattr(peer_id, 'chat_id'):
            chat_id = peer_id.chat_id
            chat_type = 'group'
        elif hasattr(peer_id, 'channel_id'):
            chat_id = peer_id.channel_id
            chat_type = 'channel'
        else:
            chat_id = peer_id.to_dict().get('chat_id', 0)
            chat_type = 'unknown'
        
        # Get chat title
        title = None
        if hasattr(chat_entity, 'title'):
            title = chat_entity.title
        elif hasattr(chat_entity, 'first_name'):
            title = f"{chat_entity.first_name or ''} {chat_entity.last_name or ''}".strip()
        elif hasattr(chat_entity, 'username'):
            title = chat_entity.username
        
        chat, created = await ChatModel.objects.aget_or_create(
            account=account,
            chat_id=chat_id,
            defaults={
                'type': 'account_chat',
                'title': title or str(chat_id),
                'chat_type': chat_type,
            }
        )
        
        if created:
            logger.info(f"Created new chat: {chat.title} ({chat_id})")
        
        return chat
    
    async def _get_or_create_user(self, from_id, sender) -> TelegramUser:
        """Get or create user"""
        if not from_id or not sender:
            return None
        
        user_id = from_id.user_id if hasattr(from_id, 'user_id') else from_id
        
        user, created = await TelegramUser.objects.aget_or_create(
            telegram_user_id=user_id,
            type='account_user',
            defaults={
                'username': getattr(sender, 'username', None),
                'first_name': getattr(sender, 'first_name', None),
                'last_name': getattr(sender, 'last_name', None),
            }
        )
        
        if not created:
            # Update user info if changed
            username = getattr(sender, 'username', None)
            first_name = getattr(sender, 'first_name', None)
            last_name = getattr(sender, 'last_name', None)
            
            if (user.username != username or 
                user.first_name != first_name or 
                user.last_name != last_name):
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                await user.asave()
        
        return user
    
    async def _save_message(self, chat: ChatModel, tg_message, direction: str):
        """Save message to database"""
        # Determine media type
        media_type = None
        if tg_message.photo:
            media_type = 'photo'
        elif tg_message.video:
            media_type = 'video'
        elif tg_message.document:
            media_type = 'document'
        elif tg_message.voice:
            media_type = 'voice'
        elif tg_message.audio:
            media_type = 'audio'
        elif tg_message.sticker:
            media_type = 'sticker'
        
        # Create message
        message = await Message.objects.acreate(
            chat=chat,
            message_id=tg_message.id,
            from_id=tg_message.from_id.user_id if tg_message.from_id else None,
            text=tg_message.text,
            direction=direction,
            reply_to_message_id=tg_message.reply_to.reply_to_msg_id if tg_message.reply_to else None,
            forwarded_from=tg_message.fwd_from.from_id.user_id if tg_message.fwd_from and tg_message.fwd_from.from_id else None,
            media_type=media_type,
            payload={
                'date': tg_message.date.isoformat(),
                'views': getattr(tg_message, 'views', None),
                'edit_date': tg_message.edit_date.isoformat() if tg_message.edit_date else None,
            }
        )
        
        # Send notification
        await NotificationService.send_message_notification('new_message', chat, message)