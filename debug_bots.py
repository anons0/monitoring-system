#!/usr/bin/env python
import os
import sys
import django

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

try:
    django.setup()
    
    from apps.bots.models import Bot
    from apps.core.encryption import encryption_service
    
    print("=== Bot Debug Information ===")
    print(f"Encryption service initialized: {encryption_service}")
    
    bots = Bot.objects.all()
    print(f"\nFound {len(bots)} bots in database:")
    
    for bot in bots:
        print(f"\nBot: @{bot.username}")
        print(f"  ID: {bot.id}")
        print(f"  Bot ID: {bot.bot_id}")
        print(f"  Status: {bot.status}")
        print(f"  Last Seen: {bot.last_seen}")
        
        # Try to decrypt the token (first few characters only for security)
        try:
            token = encryption_service.decrypt(bot.token_enc)
            print(f"  Token: {token[:10]}...")
        except Exception as e:
            print(f"  Token decrypt error: {e}")
    
    # Test starting a bot
    if bots:
        bot = bots[0]
        print(f"\n=== Testing Bot Start for @{bot.username} ===")
        
        try:
            from apps.bots.services import BotService
            
            print("Attempting to start bot...")
            result = BotService.start_bot(bot)
            print(f"Start result: {result}")
            print(f"Bot status after start: {Bot.objects.get(id=bot.id).status}")
            
        except Exception as e:
            print(f"Error starting bot: {e}")
            import traceback
            traceback.print_exc()
    
except Exception as e:
    print(f"Setup error: {e}")
    import traceback
    traceback.print_exc()
