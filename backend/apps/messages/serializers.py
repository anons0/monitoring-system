from rest_framework import serializers
from .models import Message
from apps.chats.serializers import ChatSerializer


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model"""
    chat = ChatSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'chat', 'message_id', 'from_id', 'text', 'payload',
            'direction', 'read', 'reply_to_message_id', 'forwarded_from',
            'media_type', 'media_file_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']