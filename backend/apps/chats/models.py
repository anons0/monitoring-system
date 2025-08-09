from django.db import models
from apps.core.models import BaseModel
from apps.bots.models import Bot
from apps.accounts.models import Account


class Chat(BaseModel):
    """Model for storing chat information"""
    CHAT_TYPES = (
        ('bot_chat', 'Bot Chat'),
        ('account_chat', 'Account Chat'),
    )
    
    type = models.CharField(max_length=20, choices=CHAT_TYPES)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    chat_id = models.BigIntegerField()  # Telegram chat ID
    title = models.CharField(max_length=255, null=True, blank=True)
    chat_type = models.CharField(max_length=50, null=True, blank=True)  # private, group, channel
    
    class Meta:
        db_table = 'chats'
        indexes = [
            models.Index(fields=['type', 'chat_id']),
            models.Index(fields=['bot', 'chat_id']),
            models.Index(fields=['account', 'chat_id']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(type__in=['bot_chat', 'account_chat']),
                name='valid_chat_type'
            ),
        ]

    def clean(self):
        # Ensure only one of bot or account is set based on type
        if self.type == 'bot_chat' and not self.bot:
            raise ValueError("Bot chat must have a bot assigned")
        if self.type == 'account_chat' and not self.account:
            raise ValueError("Account chat must have an account assigned")
        if self.type == 'bot_chat' and self.account:
            raise ValueError("Bot chat cannot have an account assigned")
        if self.type == 'account_chat' and self.bot:
            raise ValueError("Account chat cannot have a bot assigned")

    def __str__(self):
        entity = self.bot if self.type == 'bot_chat' else self.account
        return f"{self.title or self.chat_id} ({entity})"