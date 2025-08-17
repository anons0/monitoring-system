from django.db import models
from apps.core.models import BaseModel
from apps.chats.models import Chat


class Message(BaseModel):
    """Model for storing messages"""
    DIRECTION_CHOICES = (
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    )
    
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    message_id = models.BigIntegerField()  # Telegram message ID
    from_id = models.BigIntegerField()  # Telegram user ID who sent the message
    text = models.TextField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)  # Additional message data
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    read = models.BooleanField(default=False)
    reply_to_message_id = models.BigIntegerField(null=True, blank=True)
    forwarded_from = models.BigIntegerField(null=True, blank=True)
    media_type = models.CharField(max_length=50, null=True, blank=True)  # photo, video, document, etc.
    media_file_id = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['chat', 'created_at']),
            models.Index(fields=['chat', 'read']),
            models.Index(fields=['from_id']),
            models.Index(fields=['message_id']),
        ]

    def save(self, *args, **kwargs):
        """Override save to update chat's last_message_at"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update chat's last_message_at only when creating new messages
        if is_new:
            self.chat.last_message_at = self.created_at
            self.chat.save(update_fields=['last_message_at'])

    def __str__(self):
        preview = self.text[:50] if self.text else f"[{self.media_type}]" if self.media_type else "[Message]"
        return f"{preview} ({self.direction})"