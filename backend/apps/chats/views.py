import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from .models import Chat
from .serializers import ChatSerializer

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class ChatViewSet(viewsets.ModelViewSet):
    """ViewSet for managing chats"""
    queryset = Chat.objects.all().order_by('-created_at')
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by type
        chat_type = self.request.query_params.get('type')
        if chat_type in ['bot_chat', 'account_chat']:
            queryset = queryset.filter(type=chat_type)
        
        # Filter by entity
        bot_id = self.request.query_params.get('bot_id')
        if bot_id:
            queryset = queryset.filter(bot_id=bot_id)
        
        account_id = self.request.query_params.get('account_id')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        
        # Search by title
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        # Annotate with unread count
        queryset = queryset.annotate(
            unread_count=Count('messages', filter=Q(messages__read=False))
        )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_all_read(self, request, pk=None):
        """Mark all messages in chat as read"""
        chat = self.get_object()
        updated = chat.messages.filter(read=False).update(read=True)
        return Response({'status': 'marked_read', 'updated': updated})

@login_required
def bot_chats(request):
    """Get bot chats with unread counts"""
    try:
        chats = Chat.objects.filter(type='bot_chat').annotate(
            unread_count=Count('messages', filter=Q(messages__read=False))
        ).select_related('bot').order_by('-created_at')
        
        data = []
        for chat in chats:
            data.append({
                'id': chat.id,
                'chat_id': chat.chat_id,
                'title': chat.title,
                'chat_type': chat.chat_type,
                'bot': {
                    'id': chat.bot.id,
                    'username': chat.bot.username,
                    'status': chat.bot.status
                } if chat.bot else None,
                'unread_count': chat.unread_count,
                'created_at': chat.created_at
            })
        
        return JsonResponse({'chats': data})
        
    except Exception as e:
        logger.error(f"Error fetching bot chats: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def account_chats(request):
    """Get account chats with unread counts"""
    try:
        chats = Chat.objects.filter(type='account_chat').annotate(
            unread_count=Count('messages', filter=Q(messages__read=False))
        ).select_related('account').order_by('-created_at')
        
        data = []
        for chat in chats:
            data.append({
                'id': chat.id,
                'chat_id': chat.chat_id,
                'title': chat.title,
                'chat_type': chat.chat_type,
                'account': {
                    'id': chat.account.id,
                    'phone_number': chat.account.phone_number,
                    'status': chat.account.status
                } if chat.account else None,
                'unread_count': chat.unread_count,
                'created_at': chat.created_at
            })
        
        return JsonResponse({'chats': data})
        
    except Exception as e:
        logger.error(f"Error fetching account chats: {e}")
        return JsonResponse({'error': str(e)}, status=500)