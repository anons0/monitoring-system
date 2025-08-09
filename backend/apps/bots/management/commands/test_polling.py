import time
import logging
from django.core.management.base import BaseCommand
from apps.bots.models import Bot
from apps.bots.services import BotService
from apps.bots.aiogram_manager import AiogramManager

logger = logging.getLogger('bots')

class Command(BaseCommand):
    help = 'Test bot polling functionality'

    def add_arguments(self, parser):
        parser.add_argument('--bot-id', type=int, help='Bot ID to test')
        parser.add_argument('--duration', type=int, default=30, help='Test duration in seconds')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🤖 Testing bot polling functionality...'))
        
        # Get bot to test
        if options['bot_id']:
            try:
                bot = Bot.objects.get(id=options['bot_id'])
            except Bot.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Bot with ID {options["bot_id"]} not found'))
                return
        else:
            bots = Bot.objects.filter(status='active')
            if not bots:
                self.stdout.write(self.style.WARNING('⚠ No active bots found'))
                return
            bot = bots[0]
        
        self.stdout.write(f'\n🔍 Testing bot: @{bot.username} (ID: {bot.id})')
        self.stdout.write(f'   Status: {bot.status}')
        
        # Check if bot is in manager
        active_bots = AiogramManager.get_active_bots()
        self.stdout.write(f'   Active in manager: {"✅" if bot.id in active_bots else "❌"}')
        
        if bot.id not in active_bots:
            self.stdout.write('   Attempting to start bot...')
            if BotService.start_bot(bot):
                self.stdout.write(self.style.SUCCESS('   ✅ Bot started successfully'))
            else:
                self.stdout.write(self.style.ERROR('   ❌ Failed to start bot'))
                return
        
        # Monitor for messages
        duration = options['duration']
        self.stdout.write(f'\n📡 Monitoring for messages for {duration} seconds...')
        self.stdout.write('   Send a message to your bot to test!')
        
        # Get initial message count
        from apps.messages.models import Message
        from apps.chats.models import Chat
        
        initial_count = Message.objects.filter(
            chat__bot=bot,
            direction='incoming'
        ).count()
        
        self.stdout.write(f'   Initial message count: {initial_count}')
        
        # Wait and check periodically
        for i in range(duration):
            time.sleep(1)
            current_count = Message.objects.filter(
                chat__bot=bot,
                direction='incoming'
            ).count()
            
            if current_count > initial_count:
                new_messages = current_count - initial_count
                self.stdout.write(self.style.SUCCESS(f'   🎉 Received {new_messages} new message(s)!'))
                
                # Show latest message
                latest_message = Message.objects.filter(
                    chat__bot=bot,
                    direction='incoming'
                ).order_by('-created_at').first()
                
                if latest_message:
                    preview = latest_message.text[:50] if latest_message.text else f"[{latest_message.media_type}]"
                    self.stdout.write(f'   Latest: {preview}')
                
                break
            
            if (i + 1) % 10 == 0:
                self.stdout.write(f'   ... waiting ({i + 1}/{duration}s)')
        
        final_count = Message.objects.filter(
            chat__bot=bot,
            direction='incoming'
        ).count()
        
        if final_count > initial_count:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Polling test PASSED! Received {final_count - initial_count} message(s)'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠ No new messages received during test'))
            self.stdout.write('   This could mean:')
            self.stdout.write('   1. No one sent messages to the bot')
            self.stdout.write('   2. Polling is not working correctly')
            self.stdout.write('   3. Message handler has issues')
        
        self.stdout.write(f'\n📊 Final statistics:')
        self.stdout.write(f'   Total chats: {Chat.objects.filter(bot=bot).count()}')
        self.stdout.write(f'   Total messages: {Message.objects.filter(chat__bot=bot).count()}')
        self.stdout.write(f'   Incoming messages: {Message.objects.filter(chat__bot=bot, direction="incoming").count()}')
        self.stdout.write(f'   Outgoing messages: {Message.objects.filter(chat__bot=bot, direction="outgoing").count()}')
