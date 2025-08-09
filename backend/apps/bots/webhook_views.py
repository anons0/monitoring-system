import json
import logging
import hashlib
import hmac
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from asgiref.sync import async_to_sync
from .models import Bot
from .aiogram_manager import AiogramManager
from apps.core.encryption import encryption_service

logger = logging.getLogger('bots')

@csrf_exempt
@require_POST
def bot_webhook(request, bot_id: int, secret: str):
    """Handle bot webhook"""
    try:
        # Verify bot exists and secret
        try:
            bot = Bot.objects.get(id=bot_id)
        except Bot.DoesNotExist:
            logger.warning(f"Webhook called for non-existent bot {bot_id}")
            return HttpResponse(status=404)
        
        # Verify webhook secret matches what AiogramManager generates
        expected_secret = hashlib.sha256(f"bot_{bot_id}_webhook".encode()).hexdigest()[:32]
        if secret != expected_secret:
            logger.warning(f"Invalid webhook secret for bot {bot_id}")
            return HttpResponse(status=403)
        
        # Parse update data
        try:
            update_data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook for bot {bot_id}: {e}")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Process update asynchronously
        async_to_sync(AiogramManager.process_webhook)(bot_id, update_data)
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Error processing webhook for bot {bot_id}: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)