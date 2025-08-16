#!/usr/bin/env python3
"""
Debug script to check environment variable loading
Run this to see what's happening with your .env file
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and can be read."""
    print("🔍 Checking .env file...")
    
    # Check current working directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    # Check for .env file
    env_path = Path('.env')
    if env_path.exists():
        print(f"✅ .env file found at: {env_path.absolute()}")
        
        # Check file permissions
        try:
            with open(env_path, 'r') as f:
                first_line = f.readline().strip()
                print(f"First line of .env: {first_line}")
                print(f"File is readable: ✅")
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print(f"❌ .env file NOT found at: {env_path.absolute()}")
        
        # Check if it exists in parent directories
        parent = Path(cwd).parent
        while parent != parent.parent:
            parent_env = parent / '.env'
            if parent_env.exists():
                print(f"⚠️  .env file found in parent directory: {parent_env.absolute()}")
                break
            parent = parent.parent

def check_dotenv_installation():
    """Check if python-dotenv is installed."""
    print("\n📦 Checking python-dotenv installation...")
    
    try:
        import dotenv
        # Try to get version, but don't fail if it's not available
        try:
            version = dotenv.__version__
            print(f"✅ python-dotenv is installed: {version}")
        except AttributeError:
            print("✅ python-dotenv is installed (version unknown)")
        return True
    except ImportError:
        print("❌ python-dotenv is NOT installed")
        print("Install it with: pip install python-dotenv")
        return False

def test_dotenv_loading():
    """Test loading .env file with python-dotenv."""
    print("\n🧪 Testing dotenv loading...")
    
    try:
        from dotenv import load_dotenv
        
        # Load .env file
        result = load_dotenv()
        print(f"load_dotenv() result: {result}")
        
        # Check if environment variables are loaded
        test_vars = [
            'GEMINI_API_KEY',
            'GMAIL_CLIENT_ID', 
            'SHEETS_CLIENT_ID',
            'CALENDLY_API_KEY',
            'FIREBASE_PROJECT_ID'
        ]
        
        print("\n📋 Environment variable status:")
        for var in test_vars:
            value = os.getenv(var)
            if value:
                # Show first few characters for security
                display_value = value[:10] + "..." if len(value) > 10 else value
                print(f"  {var}: ✅ SET ({display_value})")
            else:
                print(f"  {var}: ❌ NOT SET")
                
    except Exception as e:
        print(f"❌ Error testing dotenv: {e}")

def check_manual_env_vars():
    """Check if environment variables are set manually."""
    print("\n🔧 Checking manually set environment variables...")
    
    test_vars = [
        'GEMINI_API_KEY',
        'GMAIL_CLIENT_ID', 
        'SHEETS_CLIENT_ID',
        'CALENDLY_API_KEY',
        'FIREBASE_PROJECT_ID'
    ]
    
    for var in test_vars:
        value = os.environ.get(var)  # Check os.environ directly
        if value:
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"  {var}: ✅ SET in os.environ ({display_value})")
        else:
            print(f"  {var}: ❌ NOT SET in os.environ")

def main():
    """Main debug function."""
    print("🚀 Environment Variable Debug Script")
    print("=" * 50)
    
    # Check .env file
    check_env_file()
    
    # Check dotenv installation
    dotenv_installed = check_dotenv_installation()
    
    # Test dotenv loading if available
    if dotenv_installed:
        test_dotenv_loading()
    
    # Check manual environment variables
    check_manual_env_vars()
    
    print("\n" + "=" * 50)
    print("🔧 Troubleshooting Tips:")
    print("1. Make sure .env file is in the same directory as your script")
    print("2. Install python-dotenv: pip install python-dotenv")
    print("3. Check .env file format (no spaces around =)")
    print("4. Restart your terminal/IDE after creating .env file")
    print("5. Verify .env file has correct variable names")

if __name__ == "__main__":
    main()
