#!/usr/bin/env python
"""
Quick test to verify bot message monitoring is working immediately.
Run this script to test the complete message flow.
"""

import os
import sys
import django
import time
import threading

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.bots.models import Bot
from apps.bots.services import BotService
from apps.bots.aiogram_manager import AiogramManager
from apps.messages.models import Message
from apps.chats.models import Chat

def test_bot_monitoring():
    print("🤖 Testing Bot Message Monitoring")
    print("="*50)
    
    # Get first bot
    bots = Bot.objects.all()
    if not bots:
        print("❌ No bots found. Please add a bot first.")
        return False
    
    bot = bots[0]
    print(f"📱 Testing with bot: @{bot.username} (ID: {bot.id})")
    print(f"📊 Current status: {bot.status}")
    
    # Test encryption
    print("\n🔐 Testing encryption...")
    try:
        from apps.core.encryption import encryption_service
        token = encryption_service.decrypt(bot.token_enc)
        print(f"✅ Token decryption successful: {token[:15]}...")
    except Exception as e:
        print(f"❌ Token decryption failed: {e}")
        return False
    
    # Test bot connection
    print("\n🔗 Testing bot connection...")
    try:
        test_result = BotService.test_bot(bot)
        if test_result:
            print("✅ Bot connection test passed")
        else:
            print("❌ Bot connection test failed")
            return False
    except Exception as e:
        print(f"❌ Bot connection error: {e}")
        return False
    
    # Start bot if not active
    if bot.status != 'active':
        print("\n🚀 Starting bot...")
        if BotService.start_bot(bot):
            print("✅ Bot started successfully")
        else:
            print("❌ Failed to start bot")
            return False
    else:
        print("\n✅ Bot is already active")
    
    # Check if bot is in manager
    active_bots = AiogramManager.get_active_bots()
    if bot.id in active_bots:
        print("✅ Bot is active in manager")
    else:
        print("❌ Bot not found in manager")
        return False
    
    # Get initial message count
    initial_count = Message.objects.filter(chat__bot=bot).count()
    print(f"\n📊 Initial message count: {initial_count}")
    
    # Monitor for new messages
    print("\n📡 Monitoring for messages...")
    print("💬 Send a message to your bot NOW!")
    print("⏰ Waiting 30 seconds for messages...")
    
    for i in range(30):
        current_count = Message.objects.filter(chat__bot=bot).count()
        if current_count > initial_count:
            new_messages = current_count - initial_count
            print(f"\n🎉 SUCCESS! Received {new_messages} new message(s)!")
            
            # Show latest message
            latest = Message.objects.filter(chat__bot=bot).order_by('-created_at').first()
            if latest:
                preview = latest.text[:50] if latest.text else f"[{latest.media_type}]"
                print(f"📝 Latest message: {preview}")
                print(f"👤 From user: {latest.from_id}")
                print(f"💬 In chat: {latest.chat.chat_id}")
                print(f"⏰ At: {latest.created_at}")
            
            return True
        
        print(f"⏳ Waiting... ({i+1}/30)")
        time.sleep(1)
    
    print("\n⚠️ No messages received during test period")
    print("This could mean:")
    print("1. No one sent messages to the bot")
    print("2. Polling is not working")
    print("3. Message handler has issues")
    
    return False

def show_debug_info():
    print("\n🔍 Debug Information:")
    
    # Show all bots
    bots = Bot.objects.all()
    print(f"📱 Total bots in database: {len(bots)}")
    for bot in bots:
        print(f"   - @{bot.username} (ID: {bot.id}, Status: {bot.status})")
    
    # Show active bots in manager
    active_bots = AiogramManager.get_active_bots()
    print(f"🤖 Active bots in manager: {active_bots}")
    
    # Show total messages
    total_messages = Message.objects.count()
    print(f"📨 Total messages in database: {total_messages}")
    
    # Show chats
    total_chats = Chat.objects.count()
    print(f"💬 Total chats in database: {total_chats}")

if __name__ == "__main__":
    try:
        success = test_bot_monitoring()
        show_debug_info()
        
        if success:
            print("\n🎉 TEST PASSED - Bot monitoring is working!")
        else:
            print("\n❌ TEST FAILED - Check the issues above")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
