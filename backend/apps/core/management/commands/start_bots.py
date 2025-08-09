from django.core.management.base import BaseCommand
from apps.bots.models import Bot
from apps.bots.services import BotService


class Command(BaseCommand):
    help = 'Start all active bots'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bot-id',
            type=int,
            help='Start specific bot by ID',
        )

    def handle(self, *args, **options):
        if options['bot_id']:
            try:
                bot = Bot.objects.get(id=options['bot_id'])
                if BotService.start_bot(bot):
                    self.stdout.write(
                        self.style.SUCCESS(f'Started bot @{bot.username}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to start bot @{bot.username}')
                    )
            except Bot.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Bot with ID {options["bot_id"]} not found')
                )
        else:
            bots = Bot.objects.filter(status='active')
            started = 0
            
            for bot in bots:
                if BotService.start_bot(bot):
                    started += 1
                    self.stdout.write(f'Started bot @{bot.username}')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to start bot @{bot.username}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Started {started} out of {bots.count()} bots')
            )