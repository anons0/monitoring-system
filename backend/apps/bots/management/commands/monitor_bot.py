import time
import signal
import sys
from django.core.management.base import BaseCommand
from apps.bots.models import Bot
from apps.bots.services import BotService
from apps.bots.aiogram_manager import AiogramManager
from apps.messages.models import Message


class Command(BaseCommand):
    help = 'Monitor bot for incoming messages in real-time'

    def add_arguments(self, parser):
        parser.add_argument('--bot-id', type=int, help='Bot ID to monitor')

    def handle(self, *args, **options):
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            self.stdout.write('\n🛑 Stopping monitoring...')
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        self.stdout.write(self.style.SUCCESS('🤖 Starting Real-Time Bot Monitoring'))
        self.stdout.write('='*50)
        
        # Get bot to monitor
        if options['bot_id']:
            try:
                bot = Bot.objects.get(id=options['bot_id'])
            except Bot.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Bot with ID {options["bot_id"]} not found'))
                return
        else:
            bots = Bot.objects.all()
            if not bots:
                self.stdout.write(self.style.ERROR('❌ No bots found. Add a bot first.'))
                return
            bot = bots[0]
        
        self.stdout.write(f'📱 Monitoring bot: @{bot.username} (ID: {bot.id})')
        
        # Ensure bot is started
        if bot.status != 'active':
            self.stdout.write('🔄 Starting bot...')
            if BotService.start_bot(bot):
                self.stdout.write(self.style.SUCCESS('✅ Bot started successfully'))
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to start bot'))
                return
        
        # Check if bot is active in manager
        active_bots = AiogramManager.get_active_bots()
        if bot.id not in active_bots:
            self.stdout.write(self.style.ERROR('❌ Bot not active in manager'))
            return
        
        self.stdout.write('\n📡 Monitoring for messages...')
        self.stdout.write('💬 Send a message to your bot to test!')
        self.stdout.write('🔄 Watching database for new messages...')
        self.stdout.write('⏹️  Press Ctrl+C to stop')
        self.stdout.write('-'*50)
        
        # Get initial message count
        last_message_id = 0
        initial_count = Message.objects.filter(chat__bot=bot).count()
        
        if initial_count > 0:
            last_msg = Message.objects.filter(chat__bot=bot).order_by('-id').first()
            last_message_id = last_msg.id if last_msg else 0
        
        self.stdout.write(f'📊 Initial message count: {initial_count}')
        
        message_count = 0
        
        try:
            while True:
                # Check for new messages
                new_messages = Message.objects.filter(
                    chat__bot=bot,
                    id__gt=last_message_id
                ).order_by('id')
                
                for message in new_messages:
                    message_count += 1
                    
                    # Format message info
                    direction_icon = "📥" if message.direction == "incoming" else "📤"
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
                        f'{direction_icon} {timestamp} | {chat_info} | From: {message.from_id} | {preview}'
                    )
                    
                    last_message_id = message.id
                
                # Show periodic status
                if message_count == 0:
                    # Show a heartbeat every 10 seconds
                    current_time = time.strftime("%H:%M:%S")
                    self.stdout.write(f'⏰ {current_time} | Monitoring... (Total messages: {Message.objects.filter(chat__bot=bot).count()})')
                
                time.sleep(2)  # Check every 2 seconds
        
        except KeyboardInterrupt:
            self.stdout.write('\n🛑 Monitoring stopped')
            self.stdout.write(f'📊 Total new messages received: {message_count}')
