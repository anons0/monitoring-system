import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Message
from .serializers import MessageSerializer
from apps.chats.models import Chat
from apps.bots.aiogram_manager import AiogramManager
from apps.accounts.telethon_manager import TelethonManager

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing messages"""
    queryset = Message.objects.all().order_by('-created_at')
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by chat type (bot/account)
        chat_type = self.request.query_params.get('chat_type')
        if chat_type in ['bot_chat', 'account_chat']:
            queryset = queryset.filter(chat__type=chat_type)
        
        # Filter by chat
        chat_id = self.request.query_params.get('chat_id')
        if chat_id:
            queryset = queryset.filter(chat_id=chat_id)
        
        # Filter by read status
        unread_only = self.request.query_params.get('unread_only')
        if unread_only == 'true':
            queryset = queryset.filter(read=False)
        
        # Search by text
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(text__icontains=search)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        message.read = True
        message.save()
        return Response({'status': 'marked_read'})

@login_required
@csrf_exempt
def send_message(request):
    """Send a message via bot or account"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            chat_id = data.get('chat_id')
            text = data.get('text')
            entity_type = data.get('entity_type')  # 'bot' or 'account'
            entity_id = data.get('entity_id')
            
            if not all([chat_id, text, entity_type, entity_id]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            if entity_type == 'bot':
                # Send via bot
                message = AiogramManager.send_message(entity_id, chat_id, text)
                return JsonResponse({
                    'success': True,
                    'message_id': message.message_id if hasattr(message, 'message_id') else None
                })
            elif entity_type == 'account':
                # Send via account
                message = TelethonManager.send_message(entity_id, chat_id, text)
                return JsonResponse({
                    'success': True,
                    'message_id': message.id if hasattr(message, 'id') else None
                })
            else:
                return JsonResponse({'error': 'Invalid entity_type'}, status=400)
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def edit_message(request, message_id):
    """Edit a message"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_text = data.get('text')
            
            if not new_text:
                return JsonResponse({'error': 'Text is required'}, status=400)
            
            message = Message.objects.get(id=message_id)
            chat = message.chat
            
            if chat.type == 'account_chat':
                # Edit via Telethon
                TelethonManager.edit_message(
                    chat.account.id, 
                    chat.chat_id, 
                    message.message_id, 
                    new_text
                )
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': 'Bot messages cannot be edited via API'}, status=400)
                
        except Message.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def delete_message(request, message_id):
    """Delete a message"""
    if request.method == 'POST':
        try:
            message = Message.objects.get(id=message_id)
            chat = message.chat
            
            if chat.type == 'account_chat':
                # Delete via Telethon
                TelethonManager.delete_message(
                    chat.account.id,
                    chat.chat_id,
                    message.message_id
                )
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': 'Bot messages cannot be deleted via API'}, status=400)
                
        except Message.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)