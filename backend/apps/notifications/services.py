import logging
from typing import Optional, Dict, Any
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
from apps.chats.models import Chat
from apps.messages.models import Message

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    async def send_message_notification(notification_type: str, chat: Chat, message: Message):
        """Send message-related notification"""
        try:
            # Create notification
            notification = await Notification.objects.acreate(
                type=notification_type,
                chat=chat,
                message=message,
                title=NotificationService._get_notification_title(notification_type, chat, message),
                content=NotificationService._get_notification_content(notification_type, message),
                data={
                    'chat_id': chat.id,
                    'message_id': message.id,
                    'entity_type': 'bot' if chat.type == 'bot_chat' else 'account',
                    'entity_id': chat.bot.id if chat.bot else chat.account.id if chat.account else None
                }
            )
            
            # Send WebSocket notification
            await NotificationService._send_websocket_notification(notification)
            
        except Exception as e:
            logger.error(f"Error sending message notification: {e}")
    
    @staticmethod
    def send_message_notification_sync(notification_type: str, chat: Chat, message: Message):
        """Synchronous wrapper for send_message_notification"""
        async_to_sync(NotificationService.send_message_notification)(notification_type, chat, message)
    
    @staticmethod
    async def send_entity_notification(notification_type: str, title: str, content: str, data: Dict[str, Any]):
        """Send entity-related notification (bot/account status)"""
        try:
            notification = await Notification.objects.acreate(
                type=notification_type,
                title=title,
                content=content,
                data=data
            )
            
            # Send WebSocket notification
            await NotificationService._send_websocket_notification(notification)
            
        except Exception as e:
            logger.error(f"Error sending entity notification: {e}")
    
    @staticmethod
    async def _send_websocket_notification(notification: Notification):
        """Send notification via WebSocket"""
        try:
            channel_layer = get_channel_layer()
            
            # Determine which channel to send to
            if notification.chat:
                if notification.chat.type == 'bot_chat':
                    group_name = 'bot_notifications'
                else:
                    group_name = 'account_notifications'
            else:
                # General notification - send to both
                for group in ['bot_notifications', 'account_notifications']:
                    await channel_layer.group_send(group, {
                        'type': 'notification_message',
                        'notification': {
                            'id': notification.id,
                            'type': notification.type,
                            'title': notification.title,
                            'content': notification.content,
                            'data': notification.data,
                            'created_at': notification.created_at.isoformat()
                        }
                    })
                return
            
            # Send to specific group
            await channel_layer.group_send(group_name, {
                'type': 'notification_message',
                'notification': {
                    'id': notification.id,
                    'type': notification.type,
                    'title': notification.title,
                    'content': notification.content,
                    'data': notification.data,
                    'chat_id': notification.chat.id if notification.chat else None,
                    'created_at': notification.created_at.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {e}")
    
    @staticmethod
    def _get_notification_title(notification_type: str, chat: Chat, message: Message) -> str:
        """Generate notification title"""
        chat_name = chat.title or f"Chat {chat.chat_id}"
        
        if notification_type == 'new_message':
            return f"New message in {chat_name}"
        elif notification_type == 'message_edited':
            return f"Message edited in {chat_name}"
        elif notification_type == 'message_deleted':
            return f"Message deleted in {chat_name}"
        else:
            return f"Update in {chat_name}"
    
    @staticmethod
    def _get_notification_content(notification_type: str, message: Message) -> str:
        """Generate notification content"""
        if notification_type == 'new_message':
            if message.text:
                preview = message.text[:100] + '...' if len(message.text) > 100 else message.text
                return preview
            elif message.media_type:
                return f"[{message.media_type.title()}]"
            else:
                return "New message"
        elif notification_type == 'message_edited':
            return "A message was edited"
        elif notification_type == 'message_deleted':
            return "A message was deleted"
        else:
            return "Message updated"