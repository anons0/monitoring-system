from django.core.management.base import BaseCommand
from apps.bots.models import Bot
from apps.bots.services import BotService


class Command(BaseCommand):
    help = 'Start monitoring for all inactive bots or a specific bot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bot-id',
            type=int,
            help='Start monitoring for specific bot by ID',
        )

    def handle(self, *args, **options):
        if options['bot_id']:
            try:
                bot = Bot.objects.get(id=options['bot_id'])
                if BotService.start_bot(bot):
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Started monitoring for bot @{bot.username}')
                    )
                    self.stdout.write(f'Bot is now listening for messages in chats it has access to.')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Failed to start monitoring for bot @{bot.username}')
                    )
            except Bot.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Bot with ID {options["bot_id"]} not found')
                )
        else:
            # Start all inactive bots
            bots = Bot.objects.filter(status='inactive')
            if not bots.exists():
                self.stdout.write('No inactive bots found.')
                return
                
            started = 0
            for bot in bots:
                if BotService.start_bot(bot):
                    started += 1
                    self.stdout.write(f'✅ Started bot @{bot.username}')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Failed to start bot @{bot.username}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Started {started} out of {bots.count()} bots')
            )
            
            if started > 0:
                self.stdout.write(
                    self.style.SUCCESS('🚀 Bots are now monitoring for messages!')
                )