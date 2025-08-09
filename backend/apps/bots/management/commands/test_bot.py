from django.core.management.base import BaseCommand
from apps.bots.models import Bot
from apps.bots.services import BotService
from apps.core.encryption import encryption_service


class Command(BaseCommand):
    help = 'Test bot functionality'

    def add_arguments(self, parser):
        parser.add_argument('--bot-id', type=int, help='Bot ID to test')
        parser.add_argument('--all', action='store_true', help='Test all bots')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🤖 Testing bot functionality...'))
        
        # Test encryption service
        self.test_encryption()
        
        if options['all']:
            bots = Bot.objects.all()
            if not bots:
                self.stdout.write(self.style.WARNING('⚠ No bots found in database'))
                return
        elif options['bot_id']:
            try:
                bots = [Bot.objects.get(id=options['bot_id'])]
            except Bot.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Bot with ID {options["bot_id"]} not found'))
                return
        else:
            bots = Bot.objects.all()[:1]  # Test first bot
            if not bots:
                self.stdout.write(self.style.WARNING('⚠ No bots found in database'))
                return
        
        for bot in bots:
            self.test_bot(bot)

    def test_encryption(self):
        """Test encryption service"""
        self.stdout.write('\n🔐 Testing encryption service...')
        try:
            test_data = "test_encryption_data"
            encrypted = encryption_service.encrypt(test_data)
            decrypted = encryption_service.decrypt(encrypted)
            
            if decrypted == test_data:
                self.stdout.write(self.style.SUCCESS('✓ Encryption service working correctly'))
            else:
                self.stdout.write(self.style.ERROR('❌ Encryption/decryption mismatch'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Encryption service error: {e}'))

    def test_bot(self, bot):
        """Test individual bot"""
        self.stdout.write(f'\n🤖 Testing bot: @{bot.username} (ID: {bot.id})')
        
        # Test token decryption
        try:
            token = encryption_service.decrypt(bot.token_enc)
            self.stdout.write(self.style.SUCCESS(f'✓ Token decryption successful'))
            self.stdout.write(f'   Token preview: {token[:15]}...')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Token decryption failed: {e}'))
            return
        
        # Test bot connection
        try:
            result = BotService.test_bot(bot)
            if result:
                self.stdout.write(self.style.SUCCESS('✓ Bot connection test successful'))
            else:
                self.stdout.write(self.style.ERROR('❌ Bot connection test failed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Bot test error: {e}'))
        
        # Test bot start
        self.stdout.write(f'   Current status: {bot.status}')
        if bot.status != 'active':
            try:
                self.stdout.write('   Attempting to start bot...')
                result = BotService.start_bot(bot)
                if result:
                    self.stdout.write(self.style.SUCCESS('✓ Bot started successfully'))
                else:
                    self.stdout.write(self.style.ERROR('❌ Bot start failed'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Bot start error: {e}'))
                import traceback
                self.stdout.write(f'   Traceback: {traceback.format_exc()}')
        else:
            self.stdout.write(self.style.SUCCESS('✓ Bot is already active'))

        # Show final status
        bot.refresh_from_db()
        self.stdout.write(f'   Final status: {bot.status}')
