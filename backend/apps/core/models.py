from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Base model with common fields"""
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TelegramUser(BaseModel):
    """Common model for both bot users and account users"""
    USER_TYPES = (
        ('bot_user', 'Bot User'),
        ('account_user', 'Account User'),
    )
    
    telegram_user_id = models.BigIntegerField()
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=20, choices=USER_TYPES)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['telegram_user_id', 'type']),
        ]

    def __str__(self):
        return f"{self.username or self.first_name or self.telegram_user_id} ({self.type})"