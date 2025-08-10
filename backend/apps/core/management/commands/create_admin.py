from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create initial admin user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the admin user (default: admin)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the admin user (default: admin123)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Email for the admin user',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        
        # Check if admin user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user "{username}" already exists')
            )
            return
        
        # Create superuser
        try:
            user = User.objects.create_superuser(
                username=username,
                password=password,
                email=email
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user "{username}"')
            )
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Password: {password}')
            self.stdout.write(f'Email: {email}')
            self.stdout.write('')
            self.stdout.write('You can now login at: /login/')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create admin user: {e}')
            )