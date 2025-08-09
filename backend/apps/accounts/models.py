from django.db import models
from apps.core.models import BaseModel


class Account(BaseModel):
    """Model for storing Telegram account information"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('login_required', 'Login Required'),
    )
    
    tg_user_id = models.BigIntegerField(unique=True)  # Account's Telegram user ID
    phone_number = models.CharField(max_length=20)
    api_id_enc = models.TextField()  # Encrypted API ID
    api_hash_enc = models.TextField()  # Encrypted API Hash
    session_enc = models.TextField(null=True, blank=True)  # Encrypted Telethon session
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'accounts'

    def __str__(self):
        return f"{self.phone_number} ({self.tg_user_id})"