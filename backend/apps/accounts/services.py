import asyncio
import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError
from .models import Account
from apps.core.encryption import encryption_service
from .telethon_manager import TelethonManager

logger = logging.getLogger('accounts')

class AccountService:
    """Service for managing Telegram accounts"""
    
    @staticmethod
    def add_account(phone_number: str, api_id: str, api_hash: str) -> Account:
        """Add a new account"""
        try:
            # Check if account already exists
            if Account.objects.filter(phone_number=phone_number).exists():
                raise ValueError(f"Account with phone {phone_number} already exists")
            
            # Encrypt credentials
            encrypted_api_id = encryption_service.encrypt(api_id)
            encrypted_api_hash = encryption_service.encrypt(api_hash)
            
            account = Account.objects.create(
                phone_number=phone_number,
                api_id_enc=encrypted_api_id,
                api_hash_enc=encrypted_api_hash,
                status='login_required'
            )
            
            logger.info(f"Added account {phone_number}")
            return account
            
        except Exception as e:
            logger.error(f"Failed to add account: {e}")
            raise
    
    @staticmethod
    def initiate_login(account: Account) -> Dict[str, Any]:
        """Initiate login process for account"""
        try:
            api_id = encryption_service.decrypt(account.api_id_enc)
            api_hash = encryption_service.decrypt(account.api_hash_enc)
            
            result = asyncio.run(
                AccountService._initiate_login_async(account.id, account.phone_number, api_id, api_hash)
            )
            
            if result['success']:
                account.status = 'login_required'
                account.save()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to initiate login for account {account.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    async def _initiate_login_async(account_id: int, phone_number: str, api_id: str, api_hash: str) -> Dict[str, Any]:
        """Initiate login asynchronously"""
        try:
            success = await TelethonManager.initiate_login(account_id, phone_number, api_id, api_hash)
            return {'success': success}
        except Exception as e:
            logger.error(f"Error in async login initiation: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_login(account: Account, code: str, password: Optional[str] = None) -> Dict[str, Any]:
        """Verify login code and complete authentication"""
        try:
            result = asyncio.run(
                AccountService._verify_login_async(account.id, code, password)
            )
            
            if result['success']:
                # Update account with user ID and session
                account.tg_user_id = result.get('user_id')
                account.status = 'active'
                account.last_seen = timezone.now()
                
                # Store encrypted session
                if result.get('session'):
                    account.session_enc = encryption_service.encrypt(result['session'])
                
                account.save()
                logger.info(f"Successfully logged in account {account.phone_number}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to verify login for account {account.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    async def _verify_login_async(account_id: int, code: str, password: Optional[str] = None) -> Dict[str, Any]:
        """Verify login asynchronously"""
        try:
            return await TelethonManager.verify_login(account_id, code, password)
        except Exception as e:
            logger.error(f"Error in async login verification: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def start_account(account: Account) -> bool:
        """Start an account client"""
        try:
            if not account.session_enc:
                logger.error(f"Account {account.id} has no session - login required")
                return False
            
            api_id = encryption_service.decrypt(account.api_id_enc)
            api_hash = encryption_service.decrypt(account.api_hash_enc)
            session = encryption_service.decrypt(account.session_enc)
            
            success = asyncio.run(
                TelethonManager.start_account(account.id, api_id, api_hash, session)
            )
            
            if success:
                account.status = 'active'
                account.last_seen = timezone.now()
                account.save()
                logger.info(f"Started account {account.phone_number}")
                return True
            else:
                account.status = 'error'
                account.save()
                return False
                
        except Exception as e:
            logger.error(f"Failed to start account {account.id}: {e}")
            account.status = 'error'
            account.save()
            return False
    
    @staticmethod
    def stop_account(account: Account) -> bool:
        """Stop an account client"""
        try:
            success = asyncio.run(TelethonManager.stop_account(account.id))
            
            if success:
                account.status = 'inactive'
                account.save()
                logger.info(f"Stopped account {account.phone_number}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to stop account {account.id}: {e}")
            return False
    
    @staticmethod
    def test_account(account: Account) -> bool:
        """Test account connection"""
        try:
            if not account.session_enc:
                return False
            
            result = asyncio.run(TelethonManager.test_account(account.id))
            return result
        except Exception as e:
            logger.error(f"Failed to test account {account.id}: {e}")
            return False