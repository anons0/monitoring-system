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
    
    # Profile fields
    first_name = models.CharField(max_length=255, blank=True, help_text="Bot's display name")
    description = models.TextField(blank=True, help_text="Bot description (up to 512 characters)")
    short_description = models.CharField(max_length=120, blank=True, help_text="Short description for bot (up to 120 characters)")
    profile_photo = models.ImageField(upload_to='bot_profiles/', blank=True, null=True, help_text="Bot profile photo")
    profile_photo_url = models.URLField(blank=True, help_text="Current profile photo URL from Telegram")
    # Bot commands and menu
    commands = models.JSONField(default=list, blank=True, help_text="Bot commands list")
    menu_button_text = models.CharField(max_length=64, blank=True, help_text="Menu button text")
    menu_button_url = models.URLField(blank=True, help_text="Menu button URL")
    
    # Auto-reply functionality
    auto_reply_enabled = models.BooleanField(default=True, help_text="Whether to send auto-reply to user messages")
    auto_reply_message = models.TextField(
        default='📦 Ботдан фойдаланиш тартиби\nУшбу бот фақат рўйхатдан ўтган фойдаланувчилар учун юк маълумотларини олишга мўлжалланган.\nАгар сиз рўйхатдан ўтмаган бўлсангиз, @jahon_yuklari_admin_44 га мурожаат қилинг.\n\nЮкни олиш ёки етказиш манзилида ҳар қандай ўзгариш бўлса, @jahon_yuklari_admin_4 га тўғридан-тўғри мурожаат қилинг.\n\n🚫 Бу ботга ёзманг!',
        blank=True,
        help_text="Auto-reply message to send to users (except for /start command)"
    )
    
    # Profile update tracking
    profile_last_updated = models.DateTimeField(null=True, blank=True)
    profile_update_pending = models.BooleanField(default=False, help_text="Whether profile updates are pending")

    class Meta:
        db_table = 'bots'

    def __str__(self):
        return f"@{self.username} ({self.bot_id})"
    
    @property
    def display_name(self):
        """Get display name for the bot"""
        return self.first_name or self.username or f"Bot {self.bot_id}"