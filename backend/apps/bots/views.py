import logging
import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
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

@login_required
def bot_settings(request, bot_id):
    """Display bot settings page"""
    bot = get_object_or_404(Bot, id=bot_id)
    return render(request, 'core/bot_settings.html', {'bot': bot})

@login_required
def update_basic_info(request, bot_id):
    """Update bot basic information"""
    if request.method == 'POST':
        try:
            bot = get_object_or_404(Bot, id=bot_id)
            
            # Update basic fields
            bot.first_name = request.POST.get('first_name', '')
            bot.description = request.POST.get('description', '')
            bot.short_description = request.POST.get('short_description', '')
            
            # Handle profile photo upload
            if 'profile_photo' in request.FILES:
                bot.profile_photo = request.FILES['profile_photo']
            

            
            # Mark profile as pending update
            bot.profile_update_pending = True
            bot.save()
            
            # Check if we should update on Telegram
            if request.POST.get('action') == 'save_and_update':
                try:
                    from .profile_service import BotProfileService
                    success = BotProfileService.update_bot_profile(bot)
                    if success:
                        from django.utils import timezone
                        bot.profile_update_pending = False
                        bot.profile_last_updated = timezone.now()
                        bot.save()
                        messages.success(request, 'Bot basic information updated successfully on Telegram!')
                    else:
                        messages.warning(request, 'Bot information saved locally, but failed to update on Telegram.')
                except Exception as e:
                    logger.error(f"Error updating bot profile on Telegram: {e}")
                    messages.warning(request, f'Bot information saved locally, but failed to update on Telegram: {str(e)}')
            else:
                messages.success(request, 'Bot basic information saved successfully!')
            
        except Exception as e:
            logger.error(f"Error updating bot basic info: {e}")
            messages.error(request, f'Error updating bot information: {str(e)}')
    
    return redirect('bots:bot_settings', bot_id=bot_id)

@login_required
def update_menu_button(request, bot_id):
    """Update bot menu button"""
    if request.method == 'POST':
        try:
            bot = get_object_or_404(Bot, id=bot_id)
            
            # Update menu button fields
            bot.menu_button_text = request.POST.get('menu_button_text', '')
            bot.menu_button_url = request.POST.get('menu_button_url', '')
            
            # Mark profile as pending update
            bot.profile_update_pending = True
            bot.save()
            
            # Check if we should update on Telegram
            if request.POST.get('action') == 'save_and_update':
                try:
                    from .profile_service import BotProfileService
                    success = BotProfileService.update_bot_menu_button(bot)
                    if success:
                        from django.utils import timezone
                        bot.profile_update_pending = False
                        bot.profile_last_updated = timezone.now()
                        bot.save()
                        messages.success(request, 'Menu button updated successfully on Telegram!')
                    else:
                        messages.warning(request, 'Menu button saved locally, but failed to update on Telegram.')
                except Exception as e:
                    logger.error(f"Error updating menu button on Telegram: {e}")
                    messages.warning(request, f'Menu button saved locally, but failed to update on Telegram: {str(e)}')
            else:
                messages.success(request, 'Menu button saved successfully!')
            
        except Exception as e:
            logger.error(f"Error updating menu button: {e}")
            messages.error(request, f'Error updating menu button: {str(e)}')
    
    return redirect('bots:bot_settings', bot_id=bot_id)

@login_required
def update_commands(request, bot_id):
    """Update bot commands"""
    if request.method == 'POST':
        try:
            bot = get_object_or_404(Bot, id=bot_id)
            
            # Collect commands
            commands = []
            command_names = request.POST.getlist('command_name[]')
            command_descriptions = request.POST.getlist('command_description[]')
            
            for name, description in zip(command_names, command_descriptions):
                name = name.strip()
                description = description.strip()
                if name and description:
                    commands.append({'command': name, 'description': description})
            
            bot.commands = commands
            bot.profile_update_pending = True
            bot.save()
            
            # Check if we should update on Telegram
            if request.POST.get('action') == 'save_and_update':
                try:
                    from .profile_service import BotProfileService
                    success = BotProfileService.update_bot_commands(bot)
                    if success:
                        from django.utils import timezone
                        bot.profile_update_pending = False
                        bot.profile_last_updated = timezone.now()
                        bot.save()
                        messages.success(request, 'Bot commands updated successfully on Telegram!')
                    else:
                        messages.warning(request, 'Commands saved locally, but failed to update on Telegram.')
                except Exception as e:
                    logger.error(f"Error updating commands on Telegram: {e}")
                    messages.warning(request, f'Commands saved locally, but failed to update on Telegram: {str(e)}')
            else:
                messages.success(request, 'Bot commands saved successfully!')
            
        except Exception as e:
            logger.error(f"Error updating commands: {e}")
            messages.error(request, f'Error updating commands: {str(e)}')
    
    return redirect('bots:bot_settings', bot_id=bot_id)

@login_required
def bulk_update(request):
    """Bulk update multiple bots"""
    if request.method == 'POST':
        try:
            selected_bot_ids = request.POST.getlist('selected_bots')
            if not selected_bot_ids:
                messages.error(request, 'No bots selected for update.')
                return redirect('core:bots')
            
            # Get selected bots
            bots = Bot.objects.filter(id__in=selected_bot_ids)
            if not bots.exists():
                messages.error(request, 'Selected bots not found.')
                return redirect('core:bots')
            
            # Collect update data
            update_data = {}
            
            # Basic information
            if request.POST.get('first_name'):
                update_data['first_name'] = request.POST.get('first_name')
            if request.POST.get('description'):
                update_data['description'] = request.POST.get('description')
            if request.POST.get('short_description'):
                update_data['short_description'] = request.POST.get('short_description')
            
            # Menu button
            if request.POST.get('menu_button_text'):
                update_data['menu_button_text'] = request.POST.get('menu_button_text')
            if request.POST.get('menu_button_url'):
                update_data['menu_button_url'] = request.POST.get('menu_button_url')
            
            # Commands
            command_names = request.POST.getlist('bulk_command_name[]')
            command_descriptions = request.POST.getlist('bulk_command_description[]')
            if command_names and command_descriptions:
                commands = []
                for name, description in zip(command_names, command_descriptions):
                    name = name.strip()
                    description = description.strip()
                    if name and description:
                        commands.append({'command': name, 'description': description})
                if commands:
                    update_data['commands'] = commands
            
            # Profile photo
            profile_photo = request.FILES.get('profile_photo')
            
            # Update options
            update_on_telegram = request.POST.get('update_on_telegram') == '1'
            
            # Apply updates to each bot
            updated_count = 0
            failed_count = 0
            failed_bots = []
            
            for bot in bots:
                try:
                    # Update basic fields
                    for field, value in update_data.items():
                        setattr(bot, field, value)
                    
                    # Handle profile photo
                    if profile_photo:
                        bot.profile_photo = profile_photo
                    
                    # Mark as pending update
                    bot.profile_update_pending = True
                    bot.save()
                    
                    # Update on Telegram if requested
                    if update_on_telegram:
                        try:
                            from .profile_service import BotProfileService
                            success = True
                            
                            # Update basic info if provided
                            if any(field in update_data for field in ['first_name', 'description', 'short_description']) or profile_photo:
                                success &= BotProfileService.update_bot_profile(bot)
                            
                            # Update menu button if provided
                            if any(field in update_data for field in ['menu_button_text', 'menu_button_url']):
                                success &= BotProfileService.update_bot_menu_button(bot)
                            
                            # Update commands if provided
                            if 'commands' in update_data:
                                success &= BotProfileService.update_bot_commands(bot)
                            
                            if success:
                                from django.utils import timezone
                                bot.profile_update_pending = False
                                bot.profile_last_updated = timezone.now()
                                bot.save()
                            else:
                                failed_bots.append(f"@{bot.username} (Telegram update failed)")
                                
                        except Exception as e:
                            logger.error(f"Error updating bot {bot.id} on Telegram: {e}")
                            failed_bots.append(f"@{bot.username} ({str(e)})")
                    
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error updating bot {bot.id}: {e}")
                    failed_count += 1
                    failed_bots.append(f"@{bot.username} ({str(e)})")
            
            # Show results
            if updated_count > 0:
                if update_on_telegram and not failed_bots:
                    messages.success(request, f'Successfully updated {updated_count} bot(s) on Telegram!')
                elif update_on_telegram and failed_bots:
                    messages.warning(request, f'Updated {updated_count} bot(s) locally. Some Telegram updates failed: {", ".join(failed_bots)}')
                else:
                    messages.success(request, f'Successfully updated {updated_count} bot(s) locally!')
            
            if failed_count > 0:
                messages.error(request, f'Failed to update {failed_count} bot(s): {", ".join(failed_bots)}')
            
        except Exception as e:
            logger.error(f"Error in bulk update: {e}")
            messages.error(request, f'Error during bulk update: {str(e)}')
    
    return redirect('core:bots')

@login_required
def delete_bot(request, bot_id):
    """Delete a bot"""
    if request.method == 'POST':
        try:
            bot = get_object_or_404(Bot, id=bot_id)
            bot_username = bot.username
            
            # Stop the bot first
            try:
                BotService.stop_bot(bot)
            except Exception as e:
                logger.warning(f"Error stopping bot before deletion: {e}")
            
            # Delete the bot
            bot.delete()
            
            # Return JSON response for API calls or redirect for form submissions
            if request.content_type == 'application/json' or request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': True, 'message': f'Bot @{bot_username} deleted successfully!'})
            else:
                messages.success(request, f'Bot @{bot_username} deleted successfully!')
                return redirect('core:bots')
            
        except Exception as e:
            logger.error(f"Error deleting bot: {e}")
            if request.content_type == 'application/json' or request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            else:
                messages.error(request, f'Error deleting bot: {str(e)}')
                return redirect('bots:bot_settings', bot_id=bot_id)
    
    if request.content_type == 'application/json' or request.headers.get('Content-Type') == 'application/json':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    else:
        return redirect('bots:bot_settings', bot_id=bot_id)

@login_required
def update_auto_reply(request, bot_id):
    """Update bot auto-reply settings"""
    if request.method == 'POST':
        try:
            bot = get_object_or_404(Bot, id=bot_id)
            
            # Update auto-reply settings
            bot.auto_reply_enabled = request.POST.get('auto_reply_enabled') == 'on'
            bot.auto_reply_message = request.POST.get('auto_reply_message', '')
            
            bot.save()
            messages.success(request, 'Auto-reply settings updated successfully!')
            
        except Exception as e:
            logger.error(f"Error updating auto-reply settings: {e}")
            messages.error(request, f'Error updating auto-reply settings: {str(e)}')
    
    return redirect('bots:bot_settings', bot_id=bot_id)

