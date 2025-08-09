import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Bot
from .serializers import BotSerializer
from .services import BotService

logger = logging.getLogger('bots')

@method_decorator(login_required, name='dispatch')
class BotViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bots"""
    queryset = Bot.objects.all()
    serializer_class = BotSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a bot"""
        bot = self.get_object()
        try:
            result = BotService.start_bot(bot)
            if result:
                return Response({'status': 'started'})
            else:
                return Response({'error': 'Failed to start bot'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error starting bot {bot.id}: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop a bot"""
        bot = self.get_object()
        try:
            result = BotService.stop_bot(bot)
            if result:
                return Response({'status': 'stopped'})
            else:
                return Response({'error': 'Failed to stop bot'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error stopping bot {bot.id}: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
def add_bot(request):
    """Add a new bot"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
        
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            token = data.get('token')
            
            if not token:
                return JsonResponse({'error': 'Token is required'}, status=400)
            
            bot = BotService.add_bot(token)
            return JsonResponse({
                'id': bot.id,
                'bot_id': bot.bot_id,
                'username': bot.username,
                'status': bot.status
            })
        except Exception as e:
            logger.error(f"Error adding bot: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def test_bot(request, bot_id):
    """Test bot connection"""
    try:
        bot = Bot.objects.get(id=bot_id)
        result = BotService.test_bot(bot)
        return JsonResponse({'success': result})
    except Bot.DoesNotExist:
        return JsonResponse({'error': 'Bot not found'}, status=404)
    except Exception as e:
        logger.error(f"Error testing bot {bot_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)