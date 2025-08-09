import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)

class BotNotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for bot notifications"""
    
    async def connect(self):
        # Check if user is authenticated
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        
        self.group_name = 'bot_notifications'
        
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.scope['user'].username} connected to bot notifications")
    
    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"User disconnected from bot notifications")
    
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        notification = event['notification']
        
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': notification
        }))

class AccountNotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for account notifications"""
    
    async def connect(self):
        # Check if user is authenticated
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        
        self.group_name = 'account_notifications'
        
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.scope['user'].username} connected to account notifications")
    
    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"User disconnected from account notifications")
    
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        notification = event['notification']
        
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': notification
        }))

class GeneralNotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for general notifications"""
    
    async def connect(self):
        # Check if user is authenticated
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        
        # Join both groups to receive all notifications
        await self.channel_layer.group_add('bot_notifications', self.channel_name)
        await self.channel_layer.group_add('account_notifications', self.channel_name)
        
        await self.accept()
        logger.info(f"User {self.scope['user'].username} connected to general notifications")
    
    async def disconnect(self, close_code):
        # Leave both groups
        await self.channel_layer.group_discard('bot_notifications', self.channel_name)
        await self.channel_layer.group_discard('account_notifications', self.channel_name)
        logger.info(f"User disconnected from general notifications")
    
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        notification = event['notification']
        
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': notification
        }))