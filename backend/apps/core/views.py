from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.db.models import Count, Q
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
    
    account_stats = {
        'total': Account.objects.count(),
        'active': Account.objects.filter(status='active').count(),
        'inactive': Account.objects.filter(status='inactive').count(),
    }
    
    # Get recent bot chats with unread count
    bot_chats = Chat.objects.filter(type='bot_chat').select_related('bot').annotate(
        unread_count=Count('messages', filter=Q(messages__read=False))
    ).order_by('-updated_at')[:10]
    
    # Get recent account chats with unread count
    account_chats = Chat.objects.filter(type='account_chat').select_related('account').annotate(
        unread_count=Count('messages', filter=Q(messages__read=False))
    ).order_by('-updated_at')[:10]
    
    context = {
        'bot_stats': bot_stats,
        'account_stats': account_stats,
        'bot_chats': bot_chats,
        'account_chats': account_chats,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def bots_view(request):
    """Bots management view"""
    bots = Bot.objects.all().order_by('-created_at')
    
    # Get bot chats with unread count
    bot_chats = Chat.objects.filter(type='bot_chat').select_related('bot').annotate(
        unread_count=Count('messages', filter=Q(messages__read=False))
    ).order_by('-updated_at')
    
    context = {
        'bots': bots,
        'bot_chats': bot_chats,
    }
    
    return render(request, 'core/bots.html', context)


@login_required
def accounts_view(request):
    """Accounts management view"""
    accounts = Account.objects.all().order_by('-created_at')
    
    # Get account chats with unread count
    account_chats = Chat.objects.filter(type='account_chat').select_related('account').annotate(
        unread_count=Count('messages', filter=Q(messages__read=False))
    ).order_by('-updated_at')
    
    context = {
        'accounts': accounts,
        'account_chats': account_chats,
    }
    
    return render(request, 'core/accounts.html', context)


@login_required
def chat_view(request, chat_id):
    """Individual chat view"""
    try:
        chat = Chat.objects.select_related('bot', 'account').get(id=chat_id)
        messages = Message.objects.filter(chat=chat).order_by('created_at')
        
        # Mark messages as read
        Message.objects.filter(chat=chat, read=False).update(read=True)
        
        context = {
            'chat': chat,
            'messages': messages,
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