#!/usr/bin/env python
"""Debug script to check Fernet key configuration"""

import os
import sys
import django
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.core.encryption import encryption_service
from cryptography.fernet import Fernet

def main():
    print("=== Fernet Key Debug ===")
    
    try:
        # Test encryption/decryption
        test_data = "test_bot_token_123"
        
        print(f"Original data: {test_data}")
        
        encrypted = encryption_service.encrypt(test_data)
        print(f"Encrypted data: {encrypted[:50]}...")
        
        decrypted = encryption_service.decrypt(encrypted)
        print(f"Decrypted data: {decrypted}")
        
        if test_data == decrypted:
            print("✅ Encryption/decryption working correctly!")
        else:
            print("❌ Encryption/decryption failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Solution:")
        print("1. Generate a new Fernet key:")
        print("   cd backend && python manage.py generate_fernet_key")
        print("2. Update your .env file with the generated key")
        print("3. Restart the server")

if __name__ == "__main__":
    main()