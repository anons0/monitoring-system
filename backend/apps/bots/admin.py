from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Bot


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ['username', 'display_name', 'status', 'profile_status', 'last_seen', 'created_at']
    list_filter = ['status', 'profile_update_pending', 'created_at']
    search_fields = ['username', 'first_name', 'bot_id']
    readonly_fields = ['bot_id', 'username', 'profile_photo_url', 'profile_last_updated', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('bot_id', 'username', 'token_enc', 'status', 'last_seen')
        }),
        ('Profile Settings', {
            'fields': ('first_name', 'description', 'short_description', 'profile_photo', 'profile_photo_url'),
            'description': 'Configure bot profile information that will be updated on Telegram'
        }),
        ('Commands & Menu', {
            'fields': ('commands', 'menu_button_text', 'menu_button_url'),
            'description': 'Bot commands and menu button configuration'
        }),
        ('Update Status', {
            'fields': ('profile_update_pending', 'profile_last_updated'),
            'description': 'Track profile update status'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['update_bot_profiles', 'sync_bot_info', 'mark_profile_pending']
    
    def profile_status(self, obj):
        """Display profile update status"""
        if obj.profile_update_pending:
            return format_html('<span style="color: orange;">⏳ Pending Update</span>')
        elif obj.profile_last_updated:
            return format_html('<span style="color: green;">✅ Updated</span>')
        else:
            return format_html('<span style="color: gray;">❔ Not Set</span>')
    profile_status.short_description = 'Profile Status'
    
    def update_bot_profiles(self, request, queryset):
        """Update bot profiles on Telegram"""
        from .services import BotProfileService
        updated = 0
        errors = 0
        
        for bot in queryset:
            try:
                result = BotProfileService.update_bot_profile(bot)
                if result:
                    updated += 1
                    bot.profile_update_pending = False
                    bot.profile_last_updated = timezone.now()
                    bot.save()
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                self.message_user(request, f"Error updating {bot.username}: {str(e)}", level='ERROR')
        
        if updated > 0:
            self.message_user(request, f"Successfully updated {updated} bot profile(s)")
        if errors > 0:
            self.message_user(request, f"Failed to update {errors} bot profile(s)", level='ERROR')
    
    update_bot_profiles.short_description = "Update selected bot profiles on Telegram"
    
    def sync_bot_info(self, request, queryset):
        """Sync bot information from Telegram"""
        from .services import BotService
        updated = 0
        errors = 0
        
        for bot in queryset:
            try:
                result = BotService.sync_bot_info(bot)
                if result:
                    updated += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                self.message_user(request, f"Error syncing {bot.username}: {str(e)}", level='ERROR')
        
        if updated > 0:
            self.message_user(request, f"Successfully synced {updated} bot(s)")
        if errors > 0:
            self.message_user(request, f"Failed to sync {errors} bot(s)", level='ERROR')
    
    sync_bot_info.short_description = "Sync bot information from Telegram"
    
    def mark_profile_pending(self, request, queryset):
        """Mark bot profiles as pending update"""
        updated = queryset.update(profile_update_pending=True)
        self.message_user(request, f"Marked {updated} bot profile(s) as pending update")
    
    mark_profile_pending.short_description = "Mark profiles as pending update"
    
    def save_model(self, request, obj, form, change):
        """Override save to mark profile as pending update when profile fields change"""
        if change:
            # Check if profile fields were changed
            original = Bot.objects.get(pk=obj.pk)
            profile_fields = ['first_name', 'description', 'short_description', 'profile_photo', 
                            'commands', 'menu_button_text', 'menu_button_url']
            
            profile_changed = any(
                getattr(obj, field) != getattr(original, field) 
                for field in profile_fields
            )
            
            if profile_changed:
                obj.profile_update_pending = True
        
        super().save_model(request, obj, form, change)