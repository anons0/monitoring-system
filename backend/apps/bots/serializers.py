from rest_framework import serializers
from .models import Bot


class BotSerializer(serializers.ModelSerializer):
    """Serializer for Bot model"""
    
    class Meta:
        model = Bot
        fields = ['id', 'bot_id', 'username', 'status', 'last_seen', 'created_at']
        read_only_fields = ['id', 'bot_id', 'username', 'created_at']