from rest_framework import serializers
from .models import Notification
from apps.chats.serializers import ChatSerializer
from apps.messages.serializers import MessageSerializer


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    chat = ChatSerializer(read_only=True)
    message = MessageSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'chat', 'message', 'title', 'content', 'data',
            'read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']