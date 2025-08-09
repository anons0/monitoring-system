from cryptography.fernet import Fernet
from django.conf import settings
import logging
import base64

logger = logging.getLogger(__name__)

class EncryptionService:
    """Service for encrypting/decrypting sensitive data"""
    
    def __init__(self):
        try:
            # Handle different key formats
            fernet_key = settings.FERNET_KEY
            
            if isinstance(fernet_key, str):
                # If it's a string, it might be base64 encoded or plain
                if len(fernet_key) == 44 and fernet_key.endswith('='):
                    # Looks like a proper Fernet key
                    key_bytes = fernet_key.encode()
                elif fernet_key == 'temp-key-generate-real-key-for-production':
                    # Generate a temporary key for development
                    logger.warning("Using temporary encryption key! Generate a proper key for production!")
                    key_bytes = Fernet.generate_key()
                else:
                    # Try to treat as base64
                    try:
                        key_bytes = base64.urlsafe_b64decode(fernet_key.encode())
                        if len(key_bytes) != 32:
                            raise ValueError("Invalid key length")
                        key_bytes = fernet_key.encode()
                    except:
                        # Generate a new key
                        logger.warning("Invalid FERNET_KEY format, generating new temporary key")
                        key_bytes = Fernet.generate_key()
            else:
                key_bytes = fernet_key
            
            self.cipher = Fernet(key_bytes)
            logger.info("Encryption service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            # Fall back to a generated key for development
            logger.warning("Creating temporary encryption key for this session")
            self.cipher = Fernet(Fernet.generate_key())
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string"""
        try:
            if not data:
                raise ValueError("Cannot encrypt empty data")
            return self.cipher.encrypt(data.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string"""
        try:
            if not encrypted_data:
                raise ValueError("Cannot decrypt empty data")
            return self.cipher.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            logger.error(f"Encrypted data length: {len(encrypted_data) if encrypted_data else 0}")
            raise
    
    def test(self) -> bool:
        """Test encryption/decryption functionality"""
        try:
            test_data = "test_encryption_12345"
            encrypted = self.encrypt(test_data)
            decrypted = self.decrypt(encrypted)
            return decrypted == test_data
        except Exception as e:
            logger.error(f"Encryption test failed: {e}")
            return False

# Global instance
try:
    encryption_service = EncryptionService()
except Exception as e:
    logger.error(f"Failed to create encryption service: {e}")
    raise