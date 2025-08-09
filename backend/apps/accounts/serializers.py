from rest_framework import serializers
from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for Account model"""
    
    class Meta:
        model = Account
        fields = ['id', 'tg_user_id', 'phone_number', 'status', 'last_seen', 'created_at']
        read_only_fields = ['id', 'tg_user_id', 'created_at']