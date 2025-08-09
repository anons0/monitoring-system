from django.test import TestCase
from apps.core.encryption import encryption_service


class EncryptionTestCase(TestCase):
    """Test encryption/decryption functionality"""

    def test_encrypt_decrypt(self):
        """Test that data can be encrypted and decrypted correctly"""
        original_data = "test_bot_token_123456789"
        
        # Encrypt data
        encrypted_data = encryption_service.encrypt(original_data)
        self.assertNotEqual(original_data, encrypted_data)
        
        # Decrypt data
        decrypted_data = encryption_service.decrypt(encrypted_data)
        self.assertEqual(original_data, decrypted_data)

    def test_encrypt_different_results(self):
        """Test that encrypting the same data twice gives different results"""
        data = "test_data"
        encrypted1 = encryption_service.encrypt(data)
        encrypted2 = encryption_service.encrypt(data)
        
        # Results should be different (due to randomness in encryption)
        self.assertNotEqual(encrypted1, encrypted2)
        
        # But both should decrypt to the same original data
        self.assertEqual(encryption_service.decrypt(encrypted1), data)
        self.assertEqual(encryption_service.decrypt(encrypted2), data)

    def test_encrypt_empty_string(self):
        """Test encrypting empty string"""
        original_data = ""
        encrypted_data = encryption_service.encrypt(original_data)
        decrypted_data = encryption_service.decrypt(encrypted_data)
        self.assertEqual(original_data, decrypted_data)