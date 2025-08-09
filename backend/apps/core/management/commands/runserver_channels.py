from django.core.management.base import BaseCommand
from channels.management.commands.runserver import Command as RunserverCommand


class Command(RunserverCommand):
    help = 'Run Django development server with Channels support'
    
    def handle(self, *args, **options):
        # Ensure we're using the ASGI application
        super().handle(*args, **options)