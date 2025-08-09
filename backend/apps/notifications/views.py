import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from .models import Notification
from .serializers import NotificationSerializer
from apps.chats.models import Chat

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing notifications"""
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by read status
        unread_only = self.request.query_params.get('unread_only')
        if unread_only == 'true':
            queryset = queryset.filter(read=False)
        
        # Filter by type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'status': 'marked_read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated = Notification.objects.filter(read=False).update(read=True)
        return Response({'status': 'marked_read', 'updated': updated})

def unread_counts(request):
    """Get unread counts for bots and accounts"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
        
    try:
        # Bot chats unread count
        bot_unread = Chat.objects.filter(type='bot_chat').aggregate(
            total_unread=Count('messages', filter=Q(messages__read=False))
        )['total_unread'] or 0
        
        # Account chats unread count
        account_unread = Chat.objects.filter(type='account_chat').aggregate(
            total_unread=Count('messages', filter=Q(messages__read=False))
        )['total_unread'] or 0
        
        # Notification unread count
        notification_unread = Notification.objects.filter(read=False).count()
        
        return JsonResponse({
            'bot_messages': bot_unread,
            'account_messages': account_unread,
            'notifications': notification_unread,
            'total': bot_unread + account_unread
        })
        
    except Exception as e:
        logger.error(f"Error fetching unread counts: {e}")
        return JsonResponse({'error': str(e)}, status=500)