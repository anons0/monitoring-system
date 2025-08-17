#!/usr/bin/env python
"""
Script to populate last_message_at field for existing chats
Run this after applying the migration that adds the last_message_at field
"""

import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.chats.models import Chat
from apps.messages.models import Message
from django.db.models import Max

def populate_last_message_times():
    """Populate last_message_at for all existing chats"""
    print("Populating last_message_at field for existing chats...")
    
    # Get all chats that don't have last_message_at set
    chats_to_update = Chat.objects.filter(last_message_at__isnull=True)
    
    updated_count = 0
    for chat in chats_to_update:
        # Get the latest message for this chat
        latest_message = chat.messages.order_by('-created_at').first()
        if latest_message:
            chat.last_message_at = latest_message.created_at
            chat.save(update_fields=['last_message_at'])
            updated_count += 1
            print(f"Updated chat {chat.id}: {chat.title or chat.chat_id}")
    
    print(f"Successfully updated {updated_count} chats with last message times.")

if __name__ == '__main__':
    populate_last_message_times() 