import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Bot
from .serializers import BotSerializer
from .profile_service import BotProfileService

logger = logging.getLogger('bots')

@method_decorator(login_required, name='dispatch')
class BotViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bots"""
    queryset = Bot.objects.all().order_by('-created_at')
    serializer_class = BotSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return super().get_queryset()
    
    @action(detail=True, methods=['post'])
    def update_profile(self, request, pk=None):
        """Update bot profile"""
        try:
            bot = self.get_object()
            
            # Update basic profile fields
            if 'first_name' in request.data:
                bot.first_name = request.data['first_name']
            
            if 'description' in request.data:
                bot.description = request.data['description']
            
            if 'short_description' in request.data:
                bot.short_description = request.data['short_description']
            
            if 'menu_button_text' in request.data:
                bot.menu_button_text = request.data['menu_button_text']
            
            if 'menu_button_url' in request.data:
                bot.menu_button_url = request.data['menu_button_url']
            
            # Handle profile photo upload
            if 'profile_photo' in request.FILES:
                profile_photo = request.FILES['profile_photo']
                # Save the uploaded file
                bot.profile_photo = profile_photo
            
            # Handle commands
            if 'commands' in request.data:
                try:
                    commands = json.loads(request.data['commands'])
                    bot.commands = commands
                except (json.JSONDecodeError, TypeError):
                    return Response({'error': 'Invalid commands format'}, status=400)
            
            # Mark profile as pending update
            bot.profile_update_pending = True
            bot.save()
            
            # If update_telegram is requested, update on Telegram
            if request.data.get('update_telegram') == 'true':
                try:
                    success = BotProfileService.update_bot_profile(bot)
                    if success:
                        bot.profile_update_pending = False
                        bot.profile_last_updated = timezone.now()
                        bot.save()
                        return Response({
                            'success': True,
                            'message': 'Bot profile updated successfully on Telegram'
                        })
                    else:
                        return Response({
                            'success': False,
                            'error': 'Failed to update profile on Telegram'
                        }, status=500)
                except Exception as e:
                    logger.error(f"Error updating bot profile on Telegram: {e}")
                    return Response({
                        'success': False,
                        'error': f'Error updating on Telegram: {str(e)}'
                    }, status=500)
            
            return Response({
                'success': True,
                'message': 'Bot profile updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating bot profile: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @action(detail=True, methods=['post'])
    def sync_profile(self, request, pk=None):
        """Sync bot profile from Telegram"""
        try:
            bot = self.get_object()
            success = BotProfileService.sync_bot_info(bot)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Bot profile synced successfully from Telegram'
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to sync profile from Telegram'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Error syncing bot profile: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @action(detail=True, methods=['get'])
    def profile_info(self, request, pk=None):
        """Get bot profile information from Telegram"""
        try:
            bot = self.get_object()
            info = BotProfileService.get_bot_profile_info(bot)
            
            return Response({
                'success': True,
                'data': info
            })
            
        except Exception as e:
            logger.error(f"Error getting bot profile info: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

@login_required
@csrf_exempt
def get_bot_detail(request, bot_id):
    """Get bot details for editing"""
    if request.method == 'GET':
        try:
            bot = Bot.objects.get(id=bot_id)
            
            data = {
                'id': bot.id,
                'bot_id': bot.bot_id,
                'username': bot.username,
                'first_name': bot.first_name,
                'description': bot.description,
                'short_description': bot.short_description,
                'menu_button_text': bot.menu_button_text,
                'menu_button_url': bot.menu_button_url,
                'commands': bot.commands,
                'profile_photo_url': bot.profile_photo.url if bot.profile_photo else bot.profile_photo_url,
                'status': bot.status,
                'profile_update_pending': bot.profile_update_pending,
                'profile_last_updated': bot.profile_last_updated.isoformat() if bot.profile_last_updated else None
            }
            
            return JsonResponse(data)
            
        except Bot.DoesNotExist:
            return JsonResponse({'error': 'Bot not found'}, status=404)
        except Exception as e:
            logger.error(f"Error getting bot details: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def update_bot_profile(request, bot_id):
    """Update bot profile"""
    if request.method == 'POST':
        try:
            bot = Bot.objects.get(id=bot_id)
            
            # Update basic profile fields
            if 'first_name' in request.POST:
                bot.first_name = request.POST['first_name']
            
            if 'description' in request.POST:
                bot.description = request.POST['description']
            
            if 'short_description' in request.POST:
                bot.short_description = request.POST['short_description']
            
            if 'menu_button_text' in request.POST:
                bot.menu_button_text = request.POST['menu_button_text']
            
            if 'menu_button_url' in request.POST:
                bot.menu_button_url = request.POST['menu_button_url']
            
            # Handle profile photo upload
            if 'profile_photo' in request.FILES:
                profile_photo = request.FILES['profile_photo']
                # Save the uploaded file
                bot.profile_photo = profile_photo
            
            # Handle commands
            if 'commands' in request.POST:
                try:
                    commands = json.loads(request.POST['commands'])
                    bot.commands = commands
                except (json.JSONDecodeError, TypeError):
                    return JsonResponse({'error': 'Invalid commands format'}, status=400)
            
            # Mark profile as pending update
            bot.profile_update_pending = True
            bot.save()
            
            # If update_telegram is requested, update on Telegram
            if request.POST.get('update_telegram') == 'true':
                try:
                    success = BotProfileService.update_bot_profile(bot)
                    if success:
                        from django.utils import timezone
                        bot.profile_update_pending = False
                        bot.profile_last_updated = timezone.now()
                        bot.save()
                        return JsonResponse({
                            'success': True,
                            'message': 'Bot profile updated successfully on Telegram'
                        })
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': 'Failed to update profile on Telegram'
                        }, status=500)
                except Exception as e:
                    logger.error(f"Error updating bot profile on Telegram: {e}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Error updating on Telegram: {str(e)}'
                    }, status=500)
            
            return JsonResponse({
                'success': True,
                'message': 'Bot profile updated successfully'
            })
            
        except Bot.DoesNotExist:
            return JsonResponse({'error': 'Bot not found'}, status=404)
        except Exception as e:
            logger.error(f"Error updating bot profile: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)