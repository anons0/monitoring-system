#!/usr/bin/env python3
"""
Telegram Monitoring System - Startup Script
This script helps set up and start the complete system.
"""

import os
import sys
import subprocess
import time

def run_command(command, description, check_output=False):
    """Run a command with error handling"""
    print(f"\n🔄 {description}...")
    try:
        if check_output:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout.strip()
        else:
            subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if check_output and e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Check if requirements.txt exists
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    # Install packages
    packages = [
        "Django==4.2.7",
        "djangorestframework==3.14.0", 
        "django-cors-headers==4.3.1",
        "channels==4.0.0",
        "aiogram==3.2.0",
        "telethon==1.34.0",
        "cryptography==41.0.8",
        "python-dotenv==1.0.0",
    ]
    
    failed = []
    for package in packages:
        if not run_command(f"pip install {package}", f"Installing {package.split('==')[0]}"):
            failed.append(package)
    
    if failed:
        print(f"\n⚠️ Some packages failed to install: {failed}")
        print("You may need to install these manually")
    
    return len(failed) == 0

def setup_django():
    """Setup Django application"""
    print("\n🔧 Setting up Django application...")
    
    os.chdir('backend')
    
    # Run setup command
    if not run_command("python manage.py setup_project --skip-superuser", "Setting up project"):
        return False
    
    # Check if superuser exists
    has_superuser = run_command(
        "python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); print('yes' if User.objects.filter(is_superuser=True).exists() else 'no')\"",
        "Checking for superuser",
        check_output=True
    )
    
    if has_superuser and 'yes' not in has_superuser.lower():
        print("\n👤 Creating superuser account...")
        print("Please provide admin credentials:")
        if not run_command("python manage.py createsuperuser", "Creating superuser"):
            print("⚠️ You can create a superuser later with: python manage.py createsuperuser")
    
    return True

def test_system():
    """Test system components"""
    print("\n🧪 Testing system components...")
    
    # Test encryption
    if not run_command("python manage.py shell -c \"from apps.core.encryption import encryption_service; print('✅ Encryption working' if encryption_service.test() else '❌ Encryption failed')\"", "Testing encryption"):
        return False
    
    # Test bot functionality if bots exist
    result = run_command("python manage.py test_bot", "Testing bot functionality", check_output=True)
    if result and "No bots found" in result:
        print("ℹ️ No bots configured yet - you can add them through the web interface")
    
    return True

def show_final_instructions():
    """Show final instructions to user"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\n📋 Next steps:")
    print("1. Start the server:")
    print("   cd backend")
    print("   python manage.py runserver")
    print("\n2. Open your browser to: http://127.0.0.1:8000")
    print("3. Login with your admin credentials")
    print("4. Add your first bot in the 'Bots' section")
    print("\n🤖 To add a bot:")
    print("• Get a bot token from @BotFather on Telegram")
    print("• Click 'Add New Bot' in the web interface")
    print("• Enter the token and click 'Add Bot'")
    print("• Click the ▶️ button to start the bot")
    print("\n📱 To add Telegram accounts:")
    print("• Go to Admin Panel > Accounts > Add Account")
    print("• Get API credentials from https://my.telegram.org")
    print("• Enter phone number, API ID, and API Hash")
    print("\n🔧 Configuration files:")
    print("• .env - Environment variables")
    print("• backend/db.sqlite3 - Database file")
    print("\n📖 For more help, see SETUP_GUIDE.md")
    print("="*60)

def main():
    """Main setup function"""
    print("🚀 Telegram Monitoring System Setup")
    print("="*40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check if we're in the right directory
    if not os.path.exists('backend') or not os.path.exists('requirements.txt'):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️ Some dependencies failed to install, but continuing...")
    
    # Setup Django
    if not setup_django():
        print("❌ Django setup failed")
        sys.exit(1)
    
    # Test system
    if not test_system():
        print("⚠️ Some tests failed, but system may still work")
    
    # Show final instructions
    show_final_instructions()

if __name__ == "__main__":
    main()
