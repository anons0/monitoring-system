#!/usr/bin/env python3
import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")
        return False

def main():
    """Install all required packages"""
    print("Installing required packages for Telegram Monitoring System...")
    
    packages = [
        "Django==4.2.7",
        "djangorestframework==3.14.0",
        "django-cors-headers==4.3.1",
        "channels==4.0.0",
        "channels-redis==4.1.0",
        "redis==5.0.1",
        "aiogram==3.2.0",
        "telethon==1.34.0",
        "cryptography==41.0.8",
        "python-dotenv==1.0.0",
        "psycopg2-binary==2.9.9",
        "daphne==4.0.0",
        "aioredis==2.0.1",
        "requests==2.31.0",
    ]
    
    failed_packages = []
    
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠️  Failed to install: {', '.join(failed_packages)}")
        print("You may need to install these manually.")
    else:
        print(f"\n🎉 All packages installed successfully!")
    
    print("\nNext steps:")
    print("1. Run: cd backend")
    print("2. Run: python manage.py migrate")
    print("3. Run: python manage.py createsuperuser")
    print("4. Run: python manage.py runserver")

if __name__ == "__main__":
    main()
