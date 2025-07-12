#!/usr/bin/env python3
"""
Test script to verify Telegram client setup
"""

import sys
import os
import json
from typing import Dict, List

def test_imports() -> bool:
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import requests
        print("✓ requests module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import requests: {e}")
        return False
    
    try:
        import sqlite3
        print("✓ sqlite3 module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import sqlite3: {e}")
        return False
    
    try:
        import redis
        print("✓ redis module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import redis: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import python-dotenv: {e}")
        return False
    
    try:
        import telegram
        print("✓ python-telegram-bot module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import python-telegram-bot: {e}")
        return False
    
    return True

def test_config() -> bool:
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import Config, validate_config
        print("✓ Config module imported successfully")
        
        # Test if .env file exists
        if os.path.exists('.env'):
            print("✓ .env file found")
        else:
            print("✗ .env file not found")
            return False
        
        # Test configuration validation
        try:
            validate_config()
            print("✓ Configuration validation passed")
        except ValueError as e:
            print(f"✗ Configuration validation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to test configuration: {e}")
        return False

def test_database() -> bool:
    """Test database connection"""
    print("\nTesting database...")
    
    try:
        from database import DatabaseManager
        from config import setup_logging
        
        setup_logging()
        db = DatabaseManager()
        
        # Test basic operations
        test_message = {
            'message_id': 'test_123',
            'text': 'Test message',
            'timestamp': '2024-01-01T12:00:00'
        }
        
        # Test storing pending message
        if db.store_pending_message(test_message):
            print("✓ Store pending message successful")
        else:
            print("✗ Store pending message failed")
            return False
        
        # Test getting pending messages
        pending = db.get_pending_messages(limit=1)
        if pending and len(pending) > 0:
            print("✓ Get pending messages successful")
        else:
            print("✗ Get pending messages failed")
            return False
        
        # Test removing pending message
        if db.remove_pending_message(pending[0]['id']):
            print("✓ Remove pending message successful")
        else:
            print("✗ Remove pending message failed")
            return False
        
        # Test storing sent message
        if db.store_sent_message('test_123', test_message, 'test response'):
            print("✓ Store sent message successful")
        else:
            print("✗ Store sent message failed")
            return False
        
        # Test getting stats
        stats = db.get_stats()
        if stats:
            print(f"✓ Database stats: {stats}")
        else:
            print("✗ Get database stats failed")
            return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_webhook_client() -> bool:
    """Test webhook client"""
    print("\nTesting webhook client...")
    
    try:
        from webhook_client import WebhookClient
        
        client = WebhookClient()
        print("✓ WebhookClient created successfully")
        
        # Test with a mock webhook URL (this will fail but we can test the client creation)
        test_message = {
            'message_id': 'test_123',
            'text': 'Test message',
            'timestamp': '2024-01-01T12:00:00'
        }
        
        print("✓ WebhookClient test completed (connection test skipped)")
        return True
        
    except Exception as e:
        print(f"✗ WebhookClient test failed: {e}")
        return False

def test_telegram_client() -> bool:
    """Test Telegram client initialization"""
    print("\nTesting Telegram client...")
    
    try:
        from telegram_client import TelegramClient
        
        # This will fail if config is invalid, but we can test the import
        print("✓ TelegramClient module imported successfully")
        print("✓ Telegram client test completed (full initialization skipped)")
        return True
        
    except Exception as e:
        print(f"✗ TelegramClient test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Telegram Client Setup Test")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
        ("Webhook Client", test_webhook_client),
        ("Telegram Client", test_telegram_client)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Start the service: sudo systemctl start telegram-client.service")
        print("2. Check status: ./status.sh")
        print("3. Send a test message to your Telegram bot")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure you've run the installation script: ./install.sh")
        print("2. Check that your .env file is properly configured")
        print("3. Verify all dependencies are installed")
        print("4. Check the logs for more details")
    
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 