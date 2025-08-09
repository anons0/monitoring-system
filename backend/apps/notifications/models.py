from django.db import models
from apps.core.models import BaseModel
from apps.chats.models import Chat
from apps.messages.models import Message


class Notification(BaseModel):
    """Model for storing notifications"""
    NOTIFICATION_TYPES = (
        ('new_message', 'New Message'),
        ('message_edited', 'Message Edited'),
        ('message_deleted', 'Message Deleted'),
        ('chat_updated', 'Chat Updated'),
        ('bot_status', 'Bot Status'),
        ('account_status', 'Account Status'),
    )
    
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, null=True, blank=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['read', 'created_at']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.type})"