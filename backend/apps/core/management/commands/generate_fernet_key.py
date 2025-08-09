from django.core.management.base import BaseCommand
from cryptography.fernet import Fernet


class Command(BaseCommand):
    help = 'Generate a Fernet encryption key'

    def handle(self, *args, **options):
        key = Fernet.generate_key()
        self.stdout.write(
            self.style.SUCCESS(f'Generated Fernet key: {key.decode()}')
        )
        self.stdout.write(
            'Add this to your .env file as FERNET_KEY={}'.format(key.decode())
        )