import asyncio
import logging
from typing import Dict, Optional, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError
from telethon import events
from telethon_clients.event_handler import EventHandler

logger = logging.getLogger('accounts')

class TelethonManager:
    """Manager for Telethon clients"""
    
    # Store active clients and login sessions
    _clients: Dict[int, TelegramClient] = {}
    _login_sessions: Dict[int, TelegramClient] = {}
    _handlers: Dict[int, EventHandler] = {}
    
    @classmethod
    async def initiate_login(cls, account_id: int, phone_number: str, api_id: str, api_hash: str) -> bool:
        """Initiate login process"""
        try:
            # Create temporary client for login
            client = TelegramClient(StringSession(), api_id, api_hash)
            await client.connect()
            
            # Send code request
            await client.send_code_request(phone_number)
            
            # Store client for verification step
            cls._login_sessions[account_id] = client
            
            logger.info(f"Login initiated for account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initiate login for account {account_id}: {e}")
            if account_id in cls._login_sessions:
                await cls._login_sessions[account_id].disconnect()
                del cls._login_sessions[account_id]
            return False
    
    @classmethod
    async def verify_login(cls, account_id: int, code: str, password: Optional[str] = None) -> Dict[str, Any]:
        """Verify login code and complete authentication"""
        try:
            client = cls._login_sessions.get(account_id)
            if not client:
                return {'success': False, 'error': 'No active login session'}
            
            try:
                # Try to sign in with the code
                user = await client.sign_in(code=code)
                
            except SessionPasswordNeededError:
                # 2FA is enabled, need password
                if not password:
                    return {'success': False, 'error': '2FA password required', 'requires_password': True}
                
                try:
                    user = await client.sign_in(password=password)
                except PasswordHashInvalidError:
                    return {'success': False, 'error': 'Invalid 2FA password'}
                    
            except PhoneCodeInvalidError:
                return {'success': False, 'error': 'Invalid verification code'}
            
            # Get session string
            session_string = client.session.save()
            
            # Clean up login session
            await client.disconnect()
            del cls._login_sessions[account_id]
            
            logger.info(f"Login completed for account {account_id}")
            return {
                'success': True,
                'user_id': user.id,
                'session': session_string
            }
            
        except Exception as e:
            logger.error(f"Failed to verify login for account {account_id}: {e}")
            # Clean up login session
            if account_id in cls._login_sessions:
                await cls._login_sessions[account_id].disconnect()
                del cls._login_sessions[account_id]
            return {'success': False, 'error': str(e)}
    
    @classmethod
    async def start_account(cls, account_id: int, api_id: str, api_hash: str, session_string: str) -> bool:
        """Start account client"""
        try:
            if account_id in cls._clients:
                logger.warning(f"Account {account_id} is already running")
                return True
            
            # Create client with existing session
            client = TelegramClient(StringSession(session_string), api_id, api_hash)
            await client.connect()
            
            # Verify session is valid
            try:
                me = await client.get_me()
                logger.info(f"Connected as {me.first_name} (@{me.username})")
            except Exception as e:
                logger.error(f"Session invalid for account {account_id}: {e}")
                await client.disconnect()
                return False
            
            # Set up event handlers
            handler = EventHandler(account_id)
            
            client.add_event_handler(handler.handle_new_message, events.NewMessage(incoming=True))
            client.add_event_handler(handler.handle_outgoing_message, events.NewMessage(outgoing=True))
            client.add_event_handler(handler.handle_message_edited, events.MessageEdited)
            client.add_event_handler(handler.handle_message_deleted, events.MessageDeleted)
            
            # Store client and handler
            cls._clients[account_id] = client
            cls._handlers[account_id] = handler
            
            logger.info(f"Started account client {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start account {account_id}: {e}")
            return False
    
    @classmethod
    def get_active_accounts(cls) -> list:
        """Get list of active account IDs"""
        return list(cls._clients.keys())
    
    @classmethod
    async def stop_account(cls, account_id: int) -> bool:
        """Stop account client"""
        try:
            if account_id not in cls._clients:
                logger.warning(f"Account {account_id} is not running")
                return True
            
            # Disconnect client
            client = cls._clients[account_id]
            await client.disconnect()
            
            # Remove from storage
            del cls._clients[account_id]
            if account_id in cls._handlers:
                del cls._handlers[account_id]
            
            logger.info(f"Stopped account client {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop account {account_id}: {e}")
            return False
    
    @classmethod
    async def test_account(cls, account_id: int) -> bool:
        """Test account connection"""
        try:
            client = cls._clients.get(account_id)
            if not client:
                return False
            
            # Try to get user info
            await client.get_me()
            return True
            
        except Exception as e:
            logger.error(f"Account {account_id} test failed: {e}")
            return False
    
    @classmethod
    def get_client(cls, account_id: int) -> Optional[TelegramClient]:
        """Get client instance"""
        return cls._clients.get(account_id)
    
    @classmethod
    async def send_message(cls, account_id: int, chat_id: int, text: str, **kwargs):
        """Send message via account"""
        try:
            client = cls.get_client(account_id)
            if not client:
                raise ValueError(f"Account {account_id} not found or not running")
            
            message = await client.send_message(entity=chat_id, message=text, **kwargs)
            
            # Save outgoing message to database
            from apps.chats.models import Chat
            from apps.messages.models import Message
            from apps.notifications.services import NotificationService
            
            try:
                chat_obj = await Chat.objects.aget(account_id=account_id, chat_id=chat_id)
                me = await client.get_me()
                saved_message = await Message.objects.acreate(
                    chat=chat_obj,
                    message_id=message.id,
                    from_id=me.id,
                    text=text,
                    direction='outgoing',
                    payload={
                        'sent_via': 'web_api',
                        'date': message.date.isoformat() if message.date else None
                    }
                )
                logger.info(f"✅ Saved outgoing message for account {account_id} via web API")
                
                # Send notification for the outgoing message
                try:
                    await NotificationService.send_message_notification('new_message', chat_obj, saved_message)
                    logger.info(f"📡 Sent notification for outgoing account message {saved_message.id}")
                except Exception as notification_error:
                    logger.error(f"❌ Failed to send notification for outgoing account message: {notification_error}")
                    
            except Chat.DoesNotExist:
                logger.warning(f"Chat {chat_id} not found for account {account_id}")
            except Exception as e:
                logger.error(f"Error saving outgoing message: {e}")
            
            return message
            
        except Exception as e:
            logger.error(f"Error sending message via account {account_id}: {e}")
            raise
    
    @classmethod
    async def edit_message(cls, account_id: int, chat_id: int, message_id: int, new_text: str):
        """Edit message"""
        try:
            client = cls.get_client(account_id)
            if not client:
                raise ValueError(f"Account {account_id} not found or not running")
            
            await client.edit_message(entity=chat_id, message=message_id, text=new_text)
            
            # Update message in database
            from apps.chats.models import Chat
            from apps.messages.models import Message
            
            try:
                chat_obj = await Chat.objects.aget(account_id=account_id, chat_id=chat_id)
                message_obj = await Message.objects.aget(chat=chat_obj, message_id=message_id)
                message_obj.text = new_text
                message_obj.payload.update({'edited': True})
                await message_obj.asave()
            except (Chat.DoesNotExist, Message.DoesNotExist):
                logger.warning(f"Could not update message {message_id} in database")
                
        except Exception as e:
            logger.error(f"Error editing message via account {account_id}: {e}")
            raise
    
    @classmethod
    async def delete_message(cls, account_id: int, chat_id: int, message_id: int):
        """Delete message"""
        try:
            client = cls.get_client(account_id)
            if not client:
                raise ValueError(f"Account {account_id} not found or not running")
            
            await client.delete_messages(entity=chat_id, message_ids=[message_id])
            
            # Mark message as deleted in database
            from apps.chats.models import Chat
            from apps.messages.models import Message
            
            try:
                chat_obj = await Chat.objects.aget(account_id=account_id, chat_id=chat_id)
                message_obj = await Message.objects.aget(chat=chat_obj, message_id=message_id)
                message_obj.payload.update({'deleted': True})
                await message_obj.asave()
            except (Chat.DoesNotExist, Message.DoesNotExist):
                logger.warning(f"Could not mark message {message_id} as deleted in database")
                
        except Exception as e:
            logger.error(f"Error deleting message via account {account_id}: {e}")
            raise
    
    @classmethod
    def get_active_accounts(cls) -> list:
        """Get list of active account IDs"""
        return list(cls._clients.keys())