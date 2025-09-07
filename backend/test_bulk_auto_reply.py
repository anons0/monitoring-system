#!/usr/bin/env python
"""
Test script for bulk auto reply functionality
"""
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.bots.models import Bot
from django.test import RequestFactory
from django.contrib.auth.models import User
from apps.bots.views import bulk_update
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

def test_bulk_auto_reply():
    """Test the bulk auto reply functionality"""
    print("🧪 Testing Bulk Auto Reply Functionality")
    print("=" * 50)
    
    # Check if we have any bots
    bots = Bot.objects.all()
    print(f"📊 Found {bots.count()} bots in the database")
    
    if bots.count() == 0:
        print("⚠️  No bots found. Creating test bots...")
        # Create some test bots
        test_bots = [
            {
                'bot_id': 123456789,
                'username': 'test_bot_1',
                'token_enc': 'encrypted_token_1',
                'auto_reply_enabled': True,
                'auto_reply_message': 'Default auto reply message 1'
            },
            {
                'bot_id': 987654321,
                'username': 'test_bot_2', 
                'token_enc': 'encrypted_token_2',
                'auto_reply_enabled': False,
                'auto_reply_message': 'Default auto reply message 2'
            }
        ]
        
        for bot_data in test_bots:
            bot, created = Bot.objects.get_or_create(
                bot_id=bot_data['bot_id'],
                defaults=bot_data
            )
            if created:
                print(f"✅ Created test bot: @{bot.username}")
            else:
                print(f"ℹ️  Bot already exists: @{bot.username}")
    
    # Get updated bot list
    bots = Bot.objects.all()
    print(f"\n📋 Current bots:")
    for bot in bots:
        print(f"  - @{bot.username}: auto_reply_enabled={bot.auto_reply_enabled}")
    
    # Test bulk update
    print(f"\n🔄 Testing bulk auto reply update...")
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'is_staff': True, 'is_superuser': True}
    )
    
    # Create a request factory
    factory = RequestFactory()
    
    # Create a POST request with bulk update data
    post_data = {
        'selected_bots': [str(bot.id) for bot in bots],
        'auto_reply_enabled': 'on',  # Enable auto reply
        'auto_reply_message': 'Updated bulk auto reply message for all bots!',
        'update_on_telegram': '0'  # Don't update on Telegram for testing
    }
    
    request = factory.post('/bots/bulk-update/', post_data)
    request.user = user
    
    # Add session and messages middleware
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    
    # Add messages storage
    messages = FallbackStorage(request)
    request._messages = messages
    
    try:
        # Call the bulk_update view
        response = bulk_update(request)
        
        print(f"✅ Bulk update completed successfully!")
        print(f"📤 Response status: {response.status_code}")
        
        # Check the updated bots
        print(f"\n📋 Updated bots:")
        for bot in Bot.objects.all():
            print(f"  - @{bot.username}: auto_reply_enabled={bot.auto_reply_enabled}")
            print(f"    Message: {bot.auto_reply_message[:50]}...")
        
        print(f"\n🎉 Bulk auto reply test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during bulk update test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_bulk_auto_reply()
