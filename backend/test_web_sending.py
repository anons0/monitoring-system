#!/usr/bin/env python
"""
Simple test to verify web message sending functionality
"""
import os
import sys
import django
import asyncio
import json

# Setup Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.bots.models import Bot
from apps.bots.aiogram_manager import AiogramManager
from django.test import Client
from django.contrib.auth.models import User

def test_web_api_send():
    """Test web API message sending"""
    print("🧪 Testing Web API Message Sending...")
    
    # Create test user
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_user('admin', 'admin@test.com', 'password')
        print("✅ Created test user")
    
    # Test API endpoint
    client = Client()
    client.login(username='admin', password='password')
    
    response = client.post('/api/messages/send/', {
        'chat_id': '1377513530',  # Real chat ID from database
        'text': 'Test message from web API',
        'entity_type': 'bot',
        'entity_id': '1'  # Bot ID 1
    }, content_type='application/json')
    
    print(f"API Response Status: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"✅ Web API working: {data}")
        return True
    else:
        print(f"❌ Web API failed: {response.content.decode()}")
        return False

def test_direct_send():
    """Test direct AiogramManager sending"""
    print("🧪 Testing Direct AiogramManager Sending...")
    
    async def send_test():
        try:
            result = await AiogramManager.send_message(1, 1377513530, 'Direct test message')
            print(f"✅ Direct send successful - Message ID: {result.message_id}")
            return True
        except Exception as e:
            print(f"❌ Direct send failed: {str(e)}")
            return False
    
    try:
        return asyncio.run(send_test())
    except Exception as e:
        print(f"❌ Direct send error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("TESTING MESSAGE SENDING FUNCTIONALITY")
    print("=" * 50)
    
    # Check if bot exists
    bots = Bot.objects.filter(status='active')
    if not bots.exists():
        print("❌ No active bots found. Please start bots first.")
        sys.exit(1)
    
    bot = bots.first()
    print(f"📱 Using bot: @{bot.username} (ID: {bot.id})")
    
    # Test both methods
    api_works = test_web_api_send()
    direct_works = test_direct_send()
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    print(f"Web API: {'✅ WORKING' if api_works else '❌ FAILED'}")
    print(f"Direct Send: {'✅ WORKING' if direct_works else '❌ FAILED'}")
    print("=" * 50)
    
    if api_works and direct_works:
        print("🎉 Both sending methods are working!")
    elif direct_works:
        print("⚠️  Direct sending works, but Web API has issues")
    else:
        print("🚨 Both sending methods have issues")