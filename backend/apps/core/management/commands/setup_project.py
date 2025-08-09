from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from cryptography.fernet import Fernet
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup the Telegram Monitoring System project'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Skip creating superuser',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Setting up Telegram Monitoring System...'))
        
        # Generate Fernet key if not exists
        self.setup_encryption()
        
        # Run migrations
        self.stdout.write('\n📦 Running database migrations...')
        call_command('migrate', verbosity=0)
        self.stdout.write(self.style.SUCCESS('✓ Database migrations completed'))
        
        # Collect static files
        self.stdout.write('\n🎨 Collecting static files...')
        call_command('collectstatic', '--noinput', verbosity=0)
        self.stdout.write(self.style.SUCCESS('✓ Static files collected'))
        
        # Create superuser if needed
        if not options['skip_superuser']:
            self.create_superuser()
        
        # Final instructions
        self.show_final_instructions()

    def setup_encryption(self):
        """Setup encryption key"""
        self.stdout.write('\n🔐 Setting up encryption...')
        
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '..', '.env')
        
        if not os.path.exists(env_file):
            # Create .env file with Fernet key
            key = Fernet.generate_key()
            with open(env_file, 'w') as f:
                f.write(f'FERNET_KEY={key.decode()}\n')
                f.write('DEBUG=True\n')
                f.write('SECRET_KEY=your-secret-key-here\n')
                f.write('\n# Database (uncomment for PostgreSQL/Supabase)\n')
                f.write('# DB_NAME=your_db_name\n')
                f.write('# DB_USER=your_db_user\n')
                f.write('# DB_PASSWORD=your_db_password\n')
                f.write('# DB_HOST=your_db_host\n')
                f.write('# DB_PORT=5432\n')
            
            self.stdout.write(self.style.SUCCESS(f'✓ Created .env file with encryption key'))
        else:
            self.stdout.write(self.style.WARNING('⚠ .env file already exists'))

    def create_superuser(self):
        """Create superuser if none exists"""
        self.stdout.write('\n👤 Setting up admin user...')
        
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING('⚠ Superuser already exists'))
            return
        
        try:
            call_command('createsuperuser', interactive=True)
            self.stdout.write(self.style.SUCCESS('✓ Superuser created'))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n⚠ Superuser creation skipped'))

    def show_final_instructions(self):
        """Show final setup instructions"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎉 Setup completed successfully!'))
        self.stdout.write('='*60)
        self.stdout.write('\n📋 Next steps:')
        self.stdout.write('1. Start the server: python manage.py runserver')
        self.stdout.write('2. Open your browser to: http://127.0.0.1:8000')
        self.stdout.write('3. Login with your admin credentials')
        self.stdout.write('4. Go to the "Bots" section to add your first bot')
        self.stdout.write('\n🤖 To add a bot:')
        self.stdout.write('• Get a bot token from @BotFather on Telegram')
        self.stdout.write('• Use the "Add Bot" button in the web interface')
        self.stdout.write('\n📱 For Telegram accounts (full client features):')
        self.stdout.write('• Go to Admin Panel > Accounts > Add Account')
        self.stdout.write('• You\'ll need API ID and API Hash from https://my.telegram.org')
        self.stdout.write('\n🔧 Configuration:')
        self.stdout.write('• Edit .env file to configure database and other settings')
        self.stdout.write('• For production, set DEBUG=False and configure a proper database')
        self.stdout.write('\n' + '='*60)
