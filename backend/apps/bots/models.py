from django.db import models
from apps.core.models import BaseModel


class Bot(BaseModel):
    """Model for storing bot information"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    )
    
    bot_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255)
    token_enc = models.TextField()  # Encrypted bot token
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'bots'

    def __str__(self):
        return f"@{self.username} ({self.bot_id})"