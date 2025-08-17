from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from apps.bots.models import Bot
from apps.accounts.models import Account
from apps.chats.models import Chat
from apps.messages.models import Message


@login_required
def dashboard(request):
    """Main dashboard view"""
    # Get statistics
    bot_stats = {
        'total': Bot.objects.count(),
        'active': Bot.objects.filter(status='active').count(),
        'inactive': Bot.objects.filter(status='inactive').count(),
    }
    
    # Get recent bots for bot management section
    bots = Bot.objects.all().order_by('-created_at')[:5]
    
    # Get recent bot chats with unread count, sorted by last message time
    bot_chats = Chat.objects.filter(type='bot_chat').select_related('bot').annotate(
        unread_count=Count('messages', filter=Q(messages__read=False))
    ).order_by('-last_message_at', '-updated_at')[:10]
    
    context = {
        'bot_stats': bot_stats,
        'bots': bots,
        'bot_chats': bot_chats,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def bots_view(request):
    """Bots management view"""
    bots = Bot.objects.all().order_by('-created_at')
    
    # Get bot statistics
    bot_stats = {
        'total': bots.count(),
        'active': bots.filter(status='active').count(),
        'inactive': bots.filter(status='inactive').count(),
        'error': bots.filter(status='error').count(),
    }
    
    # Get bot chats with unread count, sorted by last message time
    bot_chats = Chat.objects.filter(type='bot_chat').select_related('bot').annotate(
        unread_count=Count('messages', filter=Q(messages__read=False))
    ).order_by('-last_message_at', '-updated_at')
    
    context = {
        'bots': bots,
        'bot_stats': bot_stats,
        'bot_chats': bot_chats,
    }
    
    return render(request, 'core/bots.html', context)


@login_required
def chats_view(request):
    """All chats view"""
    # Get all bot chats with unread count and related bot info
    bot_chats = Chat.objects.filter(type='bot_chat').select_related('bot').annotate(
        unread_count=Count('messages', filter=Q(messages__read=False))
    ).order_by('-updated_at')
    
    # Get total statistics
    total_chats = bot_chats.count()
    total_unread = sum(chat.unread_count for chat in bot_chats)
    active_bots = Bot.objects.filter(status='active').count()
    
    context = {
        'bot_chats': bot_chats,
        'total_chats': total_chats,
        'total_unread': total_unread,
        'active_bots': active_bots,
    }
    
    return render(request, 'core/chats.html', context)


@login_required
def chat_view(request, chat_id):
    """Individual chat view"""
    try:
        chat = Chat.objects.select_related('bot', 'account').get(id=chat_id)
        messages = Message.objects.filter(chat=chat).order_by('created_at')
        
        # Calculate message statistics
        incoming_count = messages.filter(direction='incoming').count()
        outgoing_count = messages.filter(direction='outgoing').count()
        
        # Mark messages as read
        Message.objects.filter(chat=chat, read=False).update(read=True)
        
        context = {
            'chat': chat,
            'messages': messages,
            'incoming_count': incoming_count,
            'outgoing_count': outgoing_count,
        }
        
        return render(request, 'core/chat.html', context)
        
    except Chat.DoesNotExist:
        messages.error(request, 'Chat not found.')
        return redirect('core:dashboard')


@login_required
def start_bot(request, bot_id):
    """Start a bot"""
    if request.method == 'POST':
        try:
            bot = Bot.objects.get(id=bot_id)
            from apps.bots.services import BotService
            
            result = BotService.start_bot(bot)
            if result:
                messages.success(request, f'Bot @{bot.username} started successfully!')
            else:
                messages.error(request, f'Failed to start bot @{bot.username}')
                
        except Bot.DoesNotExist:
            messages.error(request, 'Bot not found.')
        except Exception as e:
            messages.error(request, f'Error starting bot: {str(e)}')
    
    return redirect('core:bots')


@login_required
def stop_bot(request, bot_id):
    """Stop a bot"""
    if request.method == 'POST':
        try:
            bot = Bot.objects.get(id=bot_id)
            from apps.bots.services import BotService
            
            result = BotService.stop_bot(bot)
            if result:
                messages.success(request, f'Bot @{bot.username} stopped successfully!')
            else:
                messages.error(request, f'Failed to stop bot @{bot.username}')
                
        except Bot.DoesNotExist:
            messages.error(request, 'Bot not found.')
        except Exception as e:
            messages.error(request, f'Error stopping bot: {str(e)}')
    
    return redirect('core:bots')


@login_required
def test_bot(request, bot_id):
    """Test a bot"""
    if request.method == 'POST':
        try:
            bot = Bot.objects.get(id=bot_id)
            from apps.bots.services import BotService
            
            result = BotService.test_bot(bot)
            if result:
                messages.success(request, f'Bot @{bot.username} test successful!')
            else:
                messages.error(request, f'Bot @{bot.username} test failed!')
                
        except Bot.DoesNotExist:
            messages.error(request, 'Bot not found.')
        except Exception as e:
            messages.error(request, f'Error testing bot: {str(e)}')
    
    return redirect('core:bots')


@login_required
def add_bot_view(request):
    """Add a new bot"""
    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        
        if not token:
            messages.error(request, 'Bot token is required.')
            return redirect('core:bots')
        
        try:
            from apps.bots.services import BotService
            bot = BotService.add_bot(token)
            messages.success(request, f'Bot @{bot.username} added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding bot: {str(e)}')
    
    return redirect('core:bots')


class CustomLoginView(auth_views.LoginView):
    """Custom login view"""
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        return '/dashboard/'


class CustomLogoutView(auth_views.LogoutView):
    """Custom logout view"""
    next_page = '/login/'


def is_admin(user):
    """Check if user is admin (superuser)"""
    return user.is_authenticated and user.is_superuser


@user_passes_test(is_admin)
def user_management_view(request):
    """User management view - only for admins"""
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
    }
    return render(request, 'core/users.html', context)


@user_passes_test(is_admin)
def add_user_view(request):
    """Add a new user - only for admins"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        email = request.POST.get('email', '').strip()
        is_admin = request.POST.get('is_admin') == 'on'
        
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('core:user_management')
        
        try:
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('core:user_management')
            
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                is_staff=is_admin,
                is_superuser=is_admin
            )
            
            messages.success(request, f'User "{username}" created successfully!')
            
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
    
    return redirect('core:user_management')


@user_passes_test(is_admin)
def delete_user_view(request, user_id):
    """Delete a user - only for admins"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Prevent deleting the current admin
            if user == request.user:
                messages.error(request, 'You cannot delete your own account.')
                return redirect('core:user_management')
            
            username = user.username
            user.delete()
            messages.success(request, f'User "{username}" deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
    
    return redirect('core:user_management')