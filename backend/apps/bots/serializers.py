from rest_framework import serializers
from .models import Bot

class BotSerializer(serializers.ModelSerializer):
    """Serializer for Bot model"""
    
    display_name = serializers.ReadOnlyField()
    profile_photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Bot
        fields = [
            'id', 'bot_id', 'username', 'status', 'last_seen',
            'first_name', 'description', 'short_description',
            'profile_photo', 'profile_photo_url', 'commands',
            'menu_button_text', 'menu_button_url',
            'profile_last_updated', 'profile_update_pending',
            'display_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'bot_id', 'username', 'created_at', 'updated_at']
    
    def get_profile_photo_url(self, obj):
        """Get profile photo URL"""
        if obj.profile_photo:
            return obj.profile_photo.url
        return obj.profile_photo_url or None