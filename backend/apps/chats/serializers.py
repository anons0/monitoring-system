from rest_framework import serializers
from .models import Chat
from apps.bots.serializers import BotSerializer
from apps.accounts.serializers import AccountSerializer


class ChatSerializer(serializers.ModelSerializer):
    """Serializer for Chat model"""
    bot = BotSerializer(read_only=True)
    account = AccountSerializer(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Chat
        fields = [
            'id', 'type', 'bot', 'account', 'chat_id', 'title', 'chat_type',
            'unread_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']