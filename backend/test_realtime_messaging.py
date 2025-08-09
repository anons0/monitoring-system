#!/usr/bin/env python
"""
Test script to verify real-time messaging is working for both bots and accounts.
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
from apps.accounts.models import Account
from apps.bots.services import BotService
from apps.accounts.services import AccountService
from apps.bots.aiogram_manager import AiogramManager
from apps.accounts.telethon_manager import TelethonManager
from apps.messages.models import Message
from apps.chats.models import Chat

def test_bot_realtime():
    """Test bot real-time messaging"""
    print("🤖 Testing Bot Real-Time Messaging")
    print("="*50)
    
    # Get first bot
    bots = Bot.objects.all()
    if not bots:
        print("❌ No bots found. Please add a bot first.")
        return False
    
    bot = bots[0]
    print(f"📱 Testing with bot: @{bot.username} (ID: {bot.id})")
    print(f"📊 Current status: {bot.status}")
    
    # Start bot if not active
    if bot.status != 'active':
        print("🚀 Starting bot...")
        if BotService.start_bot(bot):
            print("✅ Bot started successfully")
        else:
            print("❌ Failed to start bot")
            return False
    else:
        print("✅ Bot is already active")
    
    # Check if bot is in manager
    active_bots = AiogramManager.get_active_bots()
    if bot.id in active_bots:
        print("✅ Bot is active in manager")
    else:
        print("❌ Bot not found in manager")
        return False
    
    # Get initial message count
    initial_count = Message.objects.filter(chat__bot=bot).count()
    print(f"📊 Initial bot message count: {initial_count}")
    
    # Monitor for new messages
    print("\n📡 Monitoring for bot messages...")
    print("💬 Send a message to your bot NOW!")
    print("⏰ Waiting 30 seconds for messages...")
    
    for i in range(30):
        current_count = Message.objects.filter(chat__bot=bot).count()
        if current_count > initial_count:
            new_messages = current_count - initial_count
            print(f"\n🎉 SUCCESS! Received {new_messages} new bot message(s)!")
            
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
    
    print("⚠️ No bot messages received during test period")
    return False

def test_account_realtime():
    """Test account real-time messaging"""
    print("\n👤 Testing Account Real-Time Messaging")
    print("="*50)
    
    # Get first account
    accounts = Account.objects.all()
    if not accounts:
        print("❌ No accounts found. Please add an account first.")
        return False
    
    account = accounts[0]
    print(f"📱 Testing with account: {account.phone_number} (ID: {account.id})")
    print(f"📊 Current status: {account.status}")
    
    # Start account if not active
    if account.status != 'active':
        print("🚀 Starting account...")
        if AccountService.start_account(account):
            print("✅ Account started successfully")
        else:
            print("❌ Failed to start account")
            return False
    else:
        print("✅ Account is already active")
    
    # Check if account is in manager
    active_accounts = TelethonManager.get_active_accounts()
    if account.id in active_accounts:
        print("✅ Account is active in manager")
    else:
        print("❌ Account not found in manager")
        return False
    
    # Get initial message count
    initial_count = Message.objects.filter(chat__account=account).count()
    print(f"📊 Initial account message count: {initial_count}")
    
    # Monitor for new messages
    print("\n📡 Monitoring for account messages...")
    print("💬 Send a message to/from your account NOW!")
    print("⏰ Waiting 30 seconds for messages...")
    
    for i in range(30):
        current_count = Message.objects.filter(chat__account=account).count()
        if current_count > initial_count:
            new_messages = current_count - initial_count
            print(f"\n🎉 SUCCESS! Received {new_messages} new account message(s)!")
            
            # Show latest message
            latest = Message.objects.filter(chat__account=account).order_by('-created_at').first()
            if latest:
                preview = latest.text[:50] if latest.text else f"[{latest.media_type}]"
                print(f"📝 Latest message: {preview}")
                print(f"👤 From user: {latest.from_id}")
                print(f"💬 In chat: {latest.chat.chat_id}")
                print(f"⏰ At: {latest.created_at}")
            
            return True
        
        print(f"⏳ Waiting... ({i+1}/30)")
        time.sleep(1)
    
    print("⚠️ No account messages received during test period")
    return False

def show_debug_info():
    """Show debug information"""
    print("\n🔍 Debug Information:")
    
    # Show all bots
    bots = Bot.objects.all()
    print(f"📱 Total bots in database: {len(bots)}")
    for bot in bots:
        print(f"   - @{bot.username} (ID: {bot.id}, Status: {bot.status})")
    
    # Show active bots in manager
    active_bots = AiogramManager.get_active_bots()
    print(f"🤖 Active bots in manager: {active_bots}")
    
    # Show all accounts
    accounts = Account.objects.all()
    print(f"👤 Total accounts in database: {len(accounts)}")
    for account in accounts:
        print(f"   - {account.phone_number} (ID: {account.id}, Status: {account.status})")
    
    # Show active accounts in manager
    active_accounts = TelethonManager.get_active_accounts()
    print(f"👥 Active accounts in manager: {active_accounts}")
    
    # Show total messages
    total_bot_messages = Message.objects.filter(chat__bot__isnull=False).count()
    total_account_messages = Message.objects.filter(chat__account__isnull=False).count()
    print(f"📨 Total bot messages: {total_bot_messages}")
    print(f"📨 Total account messages: {total_account_messages}")
    
    # Show chats
    total_bot_chats = Chat.objects.filter(bot__isnull=False).count()
    total_account_chats = Chat.objects.filter(account__isnull=False).count()
    print(f"💬 Total bot chats: {total_bot_chats}")
    print(f"💬 Total account chats: {total_account_chats}")

if __name__ == "__main__":
    try:
        print("🚀 Starting Real-Time Messaging Test")
        print("="*60)
        
        # Test bot real-time messaging
        bot_success = test_bot_realtime()
        
        # Test account real-time messaging
        account_success = test_account_realtime()
        
        # Show debug info
        show_debug_info()
        
        # Final results
        print("\n" + "="*60)
        print("📊 FINAL RESULTS:")
        print(f"   🤖 Bot Real-Time: {'✅ WORKING' if bot_success else '❌ NOT WORKING'}")
        print(f"   👤 Account Real-Time: {'✅ WORKING' if account_success else '❌ NOT WORKING'}")
        
        if bot_success and account_success:
            print("\n🎉 ALL TESTS PASSED - Real-time messaging is working!")
        elif bot_success or account_success:
            print("\n⚠️ PARTIAL SUCCESS - Some real-time messaging is working")
        else:
            print("\n❌ ALL TESTS FAILED - Real-time messaging needs debugging")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
