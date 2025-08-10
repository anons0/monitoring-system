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
        
        # Filter messages after a certain ID (for incremental loading)
        after = self.request.query_params.get('after')
        if after:
            try:
                queryset = queryset.filter(id__gt=int(after))
            except (ValueError, TypeError):
                pass
        
        # Filter by read status
        unread_only = self.request.query_params.get('unread_only')
        if unread_only == 'true':
            queryset = queryset.filter(read=False)
        
        # Search by text
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(text__icontains=search)
        
        # Optimize with select_related
        queryset = queryset.select_related('chat', 'chat__bot', 'chat__account')
        
        # Limit results for performance
        limit = self.request.query_params.get('limit', '50')
        try:
            limit = min(int(limit), 100)  # Max 100 messages
            queryset = queryset[:limit]
        except (ValueError, TypeError):
            queryset = queryset[:50]  # Default 50 messages
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        message.read = True
        message.save()
        return Response({'status': 'marked_read'})

@csrf_exempt
@login_required
def send_message(request):
    """Send a message via bot or account"""
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
                
            chat_id = data.get('chat_id')
            text = data.get('text')
            entity_type = data.get('entity_type')  # 'bot' or 'account'
            entity_id = data.get('entity_id')
            
            if not all([chat_id, text, entity_type, entity_id]):
                logger.error(f"Missing required fields - chat_id: {chat_id}, text: {text}, entity_type: {entity_type}, entity_id: {entity_id}")
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            if entity_type == 'bot':
                # Send via bot using async with timeout
                import asyncio
                try:
                    # Create async function with timeout and better error handling
                    async def send_with_timeout():
                        try:
                            # Ensure bot is active and accessible
                            from apps.bots.models import Bot as BotModel
                            bot = await asyncio.to_thread(BotModel.objects.get, id=entity_id, status='active')
                            logger.info(f"Sending message via bot {bot.username} to chat {chat_id}")
                            
                            return await asyncio.wait_for(
                                AiogramManager.send_message(entity_id, chat_id, text),
                                timeout=30.0  # Increased timeout to 30 seconds for bot creation
                            )
                        except BotModel.DoesNotExist:
                            logger.error(f"Bot {entity_id} not found or not active")
                            raise ValueError(f"Bot {entity_id} not found or not active")
                    
                    message = asyncio.run(send_with_timeout())
                    return JsonResponse({
                        'success': True,
                        'message_id': message.message_id if hasattr(message, 'message_id') else None
                    })
                except asyncio.TimeoutError:
                    logger.error(f"Timeout sending bot message to chat {chat_id}")
                    return JsonResponse({'error': 'Message sending timed out'}, status=504)
                except ValueError as e:
                    logger.error(f"Bot error: {e}")
                    return JsonResponse({'error': str(e)}, status=400)
                except Exception as e:
                    logger.error(f"Error sending bot message: {e}")
                    return JsonResponse({'error': f'Failed to send bot message: {str(e)}'}, status=500)
                    
            elif entity_type == 'account':
                # Send via account using async with timeout
                import asyncio
                try:
                    # Create async function with timeout and better error handling
                    async def send_account_with_timeout():
                        try:
                            # Ensure account is active and accessible
                            from apps.accounts.models import Account as AccountModel
                            account = await asyncio.to_thread(AccountModel.objects.get, id=entity_id, status='active')
                            logger.info(f"Sending message via account {account.phone} to chat {chat_id}")
                            
                            return await asyncio.wait_for(
                                TelethonManager.send_message(entity_id, chat_id, text),
                                timeout=30.0  # Increased timeout to 30 seconds for account creation
                            )
                        except AccountModel.DoesNotExist:
                            logger.error(f"Account {entity_id} not found or not active")
                            raise ValueError(f"Account {entity_id} not found or not active")
                    
                    message = asyncio.run(send_account_with_timeout())
                    return JsonResponse({
                        'success': True,
                        'message_id': message.id if hasattr(message, 'id') else None
                    })
                except asyncio.TimeoutError:
                    logger.error(f"Timeout sending account message to chat {chat_id}")
                    return JsonResponse({'error': 'Message sending timed out'}, status=504)
                except ValueError as e:
                    logger.error(f"Account error: {e}")
                    return JsonResponse({'error': str(e)}, status=400)
                except Exception as e:
                    logger.error(f"Error sending account message: {e}")
                    return JsonResponse({'error': f'Failed to send account message: {str(e)}'}, status=500)
            else:
                return JsonResponse({'error': 'Invalid entity_type'}, status=400)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
                import asyncio
                try:
                    asyncio.run(TelethonManager.edit_message(
                        chat.account.id, 
                        chat.chat_id, 
                        message.message_id, 
                        new_text
                    ))
                    return JsonResponse({'success': True})
                except Exception as e:
                    logger.error(f"Error editing message via Telethon: {e}")
                    raise
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
                import asyncio
                try:
                    asyncio.run(TelethonManager.delete_message(
                        chat.account.id,
                        chat.chat_id,
                        message.message_id
                    ))
                    return JsonResponse({'success': True})
                except Exception as e:
                    logger.error(f"Error deleting message via Telethon: {e}")
                    raise
            else:
                return JsonResponse({'error': 'Bot messages cannot be deleted via API'}, status=400)
                
        except Message.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)