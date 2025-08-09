import time
import signal
import sys
from django.core.management.base import BaseCommand
from apps.bots.models import Bot
from apps.accounts.models import Account
from apps.bots.services import BotService
from apps.accounts.services import AccountService
from apps.bots.aiogram_manager import AiogramManager
from apps.accounts.telethon_manager import TelethonManager
from apps.messages.models import Message
from apps.chats.models import Chat

class Command(BaseCommand):
    help = 'Monitor both bots and accounts for incoming messages in real-time'

    def add_arguments(self, parser):
        parser.add_argument('--bot-id', type=int, help='Specific bot ID to monitor')
        parser.add_argument('--account-id', type=int, help='Specific account ID to monitor')
        parser.add_argument('--type', choices=['bots', 'accounts', 'all'], default='all', 
                           help='Type of entities to monitor')

    def handle(self, *args, **options):
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            self.stdout.write('\n🛑 Stopping monitoring...')
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        self.stdout.write(self.style.SUCCESS('📡 Starting Real-Time Message Monitoring'))
        self.stdout.write('='*60)
        
        # Determine what to monitor
        monitor_bots = options['type'] in ['bots', 'all']
        monitor_accounts = options['type'] in ['accounts', 'all']
        
        # Get entities to monitor
        monitored_bots = []
        monitored_accounts = []
        
        if monitor_bots:
            if options['bot_id']:
                try:
                    bot = Bot.objects.get(id=options['bot_id'])
                    monitored_bots = [bot]
                except Bot.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'❌ Bot with ID {options["bot_id"]} not found'))
                    return
            else:
                monitored_bots = list(Bot.objects.all())
        
        if monitor_accounts:
            if options['account_id']:
                try:
                    account = Account.objects.get(id=options['account_id'])
                    monitored_accounts = [account]
                except Account.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'❌ Account with ID {options["account_id"]} not found'))
                    return
            else:
                monitored_accounts = list(Account.objects.all())
        
        # Display what we're monitoring
        self.stdout.write(f'\n📊 Monitoring Configuration:')
        if monitored_bots:
            self.stdout.write(f'   🤖 Bots: {len(monitored_bots)}')
            for bot in monitored_bots:
                self.stdout.write(f'      - @{bot.username} (ID: {bot.id}, Status: {bot.status})')
        
        if monitored_accounts:
            self.stdout.write(f'   👤 Accounts: {len(monitored_accounts)}')
            for account in monitored_accounts:
                self.stdout.write(f'      - {account.phone_number} (ID: {account.id}, Status: {account.status})')
        
        # Start inactive entities
        self._start_inactive_entities(monitored_bots, monitored_accounts)
        
        # Check manager status
        self._check_manager_status(monitored_bots, monitored_accounts)
        
        # Get initial message counts
        last_message_ids = {}
        
        for bot in monitored_bots:
            last_msg = Message.objects.filter(chat__bot=bot).order_by('-id').first()
            last_message_ids[f'bot_{bot.id}'] = last_msg.id if last_msg else 0
        
        for account in monitored_accounts:
            last_msg = Message.objects.filter(chat__account=account).order_by('-id').first()
            last_message_ids[f'account_{account.id}'] = last_msg.id if last_msg else 0
        
        self.stdout.write(f'\n📡 Starting real-time monitoring...')
        self.stdout.write('💬 Send messages to monitored bots/accounts to see them appear here!')
        self.stdout.write('⏰ Checking every 2 seconds...\n')
        
        try:
            while True:
                new_messages_found = False
                
                # Check for new bot messages
                for bot in monitored_bots:
                    key = f'bot_{bot.id}'
                    new_messages = Message.objects.filter(
                        chat__bot=bot,
                        id__gt=last_message_ids[key]
                    ).order_by('id')
                    
                    for message in new_messages:
                        self._display_message(message, 'BOT')
                        last_message_ids[key] = message.id
                        new_messages_found = True
                
                # Check for new account messages
                for account in monitored_accounts:
                    key = f'account_{account.id}'
                    new_messages = Message.objects.filter(
                        chat__account=account,
                        id__gt=last_message_ids[key]
                    ).order_by('id')
                    
                    for message in new_messages:
                        self._display_message(message, 'ACCOUNT')
                        last_message_ids[key] = message.id
                        new_messages_found = True
                
                # Show periodic heartbeat if no messages
                if not new_messages_found:
                    current_time = time.strftime("%H:%M:%S")
                    total_messages = sum([
                        Message.objects.filter(chat__bot=bot).count() for bot in monitored_bots
                    ]) + sum([
                        Message.objects.filter(chat__account=account).count() for account in monitored_accounts
                    ])
                    self.stdout.write(f'⏰ {current_time} | Monitoring... (Total messages: {total_messages})')
                
                time.sleep(2)  # Check every 2 seconds
        
        except KeyboardInterrupt:
            self.stdout.write('\n🛑 Monitoring stopped by user')
    
    def _start_inactive_entities(self, bots, accounts):
        """Start inactive bots and accounts"""
        self.stdout.write('\n🚀 Starting inactive entities...')
        
        # Start bots
        for bot in bots:
            if bot.status != 'active':
                self.stdout.write(f'   Starting bot @{bot.username}...')
                if BotService.start_bot(bot):
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Bot @{bot.username} started'))
                else:
                    self.stdout.write(self.style.ERROR(f'   ❌ Failed to start bot @{bot.username}'))
        
        # Start accounts
        for account in accounts:
            if account.status != 'active':
                self.stdout.write(f'   Starting account {account.phone_number}...')
                if AccountService.start_account(account):
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Account {account.phone_number} started'))
                else:
                    self.stdout.write(self.style.ERROR(f'   ❌ Failed to start account {account.phone_number}'))
    
    def _check_manager_status(self, bots, accounts):
        """Check if entities are active in managers"""
        self.stdout.write('\n🔍 Checking manager status...')
        
        # Check bot manager
        active_bots = AiogramManager.get_active_bots()
        for bot in bots:
            status = "✅" if bot.id in active_bots else "❌"
            self.stdout.write(f'   {status} Bot @{bot.username} in AiogramManager')
        
        # Check account manager
        active_accounts = TelethonManager.get_active_accounts()
        for account in accounts:
            status = "✅" if account.id in active_accounts else "❌"
            self.stdout.write(f'   {status} Account {account.phone_number} in TelethonManager')
    
    def _display_message(self, message, entity_type):
        """Display a message in a formatted way"""
        # Direction icon
        direction_icon = "📥" if message.direction == "incoming" else "📤"
        
        # Entity info
        if entity_type == 'BOT':
            entity_info = f"Bot @{message.chat.bot.username}"
        else:
            entity_info = f"Account {message.chat.account.phone_number}"
        
        # Chat info
        chat_info = f"Chat {message.chat.chat_id}"
        if message.chat.title:
            chat_info = f"{message.chat.title} ({message.chat.chat_id})"
        
        # Message preview
        if message.text:
            preview = message.text[:100] + "..." if len(message.text) > 100 else message.text
        elif message.media_type:
            preview = f"[{message.media_type.upper()}]"
        else:
            preview = "[Message]"
        
        timestamp = message.created_at.strftime("%H:%M:%S")
        
        self.stdout.write(
            f'{direction_icon} {timestamp} | {entity_type} | {entity_info} | {chat_info} | From: {message.from_id} | {preview}'
        )
