#!/usr/bin/env python
"""
Startup script for the monitoring system.
This script handles proper server startup with environment checks.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_virtual_env():
    """Check if virtual environment is activated"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['django', 'daphne', 'channels', 'telethon', 'aiogram']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def run_migrations():
    """Run Django migrations"""
    print("🔄 Running Django migrations...")
    backend_dir = os.path.join(os.getcwd(), 'backend')
    
    if not os.path.exists(backend_dir):
        print(f"❌ Backend directory not found: {backend_dir}")
        return False
    
    original_dir = os.getcwd()
    try:
        os.chdir(backend_dir)
        result = subprocess.run([sys.executable, 'manage.py', 'migrate'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Migration failed: {result.stderr}")
            return False
        print("✅ Migrations completed successfully")
        return True
    finally:
        os.chdir(original_dir)

def start_daphne_server(port=8000):
    """Start the Daphne ASGI server"""
    print(f"🚀 Starting Daphne server on port {port}...")
    backend_dir = os.path.join(os.getcwd(), 'backend')
    
    if not os.path.exists(backend_dir):
        print(f"❌ Backend directory not found: {backend_dir}")
        return
    
    original_dir = os.getcwd()
    try:
        os.chdir(backend_dir)
        # Start the server
        subprocess.run([
            sys.executable, '-m', 'daphne', 
            '-p', str(port), 
            'project.asgi:application'
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
    finally:
        os.chdir(original_dir)

def main():
    """Main startup function"""
    print("🔍 Monitoring System Startup Script")
    print("=" * 40)
    
    # Check virtual environment
    if not check_virtual_env():
        print("⚠️  Warning: Virtual environment not detected")
        print("   It's recommended to run this in a virtual environment")
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("   Please install them with: pip install -r requirements.txt")
        return 1
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Run migrations
    if not run_migrations():
        return 1
    
    # Start server
    start_daphne_server()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
