#!/usr/bin/env python3
"""
Debug script for JSON parsing errors in the Telegram Monitoring System
"""

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
    from apps.bots.services import BotService
    import json
    
    print("🔍 Debugging JSON Error in Bot Activation")
    print("="*50)
    
    # Test encryption service
    print("\n1. Testing Encryption Service:")
    try:
        test_result = encryption_service.test()
        print(f"   ✅ Encryption test: {'PASSED' if test_result else 'FAILED'}")
    except Exception as e:
        print(f"   ❌ Encryption error: {e}")
    
    # Check bots in database
    print("\n2. Checking Bots in Database:")
    bots = Bot.objects.all()
    print(f"   Found {len(bots)} bots")
    
    for bot in bots:
        print(f"\n   Bot: @{bot.username}")
        print(f"   ID: {bot.id}")
        print(f"   Status: {bot.status}")
        
        # Test token decryption
        try:
            token = encryption_service.decrypt(bot.token_enc)
            print(f"   ✅ Token decryption: SUCCESS")
            print(f"   Token preview: {token[:15]}...")
        except Exception as e:
            print(f"   ❌ Token decryption: FAILED - {e}")
            continue
        
        # Test bot connection
        try:
            connection_test = BotService.test_bot(bot)
            print(f"   ✅ Bot connection: {'SUCCESS' if connection_test else 'FAILED'}")
        except Exception as e:
            print(f"   ❌ Bot connection: ERROR - {e}")
        
        # Test bot start (but don't actually start it)
        print(f"   Current status: {bot.status}")
        if bot.status != 'active':
            print("   Would attempt to start bot (not actually starting)")
        else:
            print("   Bot is already active")
    
    # Test JSON response simulation
    print("\n3. Testing JSON Response Format:")
    try:
        # Simulate the response that should be returned
        test_response = {
            'status': 'started',
            'bot_id': 1,
            'message': 'Bot started successfully'
        }
        json_str = json.dumps(test_response)
        parsed = json.loads(json_str)
        print(f"   ✅ JSON serialization: SUCCESS")
        print(f"   Sample response: {json_str}")
    except Exception as e:
        print(f"   ❌ JSON error: {e}")
    
    # Check for common issues
    print("\n4. Common Issues Check:")
    
    # Check if CSRF token might be missing
    print("   🔍 Check CSRF token in templates")
    print("   🔍 Check if forms are using POST method")
    print("   🔍 Check if Django is returning HTML error pages instead of JSON")
    
    print("\n5. Recommendations:")
    print("   1. Use browser developer tools to check actual HTTP response")
    print("   2. Check Django logs for error messages")
    print("   3. Ensure all dependencies are installed")
    print("   4. Try using form submission instead of AJAX")
    
    print("\n✅ Debug completed. Check the output above for issues.")
    
except Exception as e:
    print(f"❌ Setup error: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n🔧 Troubleshooting steps:")
    print("1. Ensure you're running from the project root directory")
    print("2. Check if all dependencies are installed: pip install -r requirements.txt")
    print("3. Run: cd backend && python manage.py check")
    print("4. Try: python start_system.py")
