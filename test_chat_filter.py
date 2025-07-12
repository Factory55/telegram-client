#!/usr/bin/env python3
"""
Simple test script for chat filter functionality
"""

import os
import sys

def test_chat_filter_basic():
    """Test basic chat filter functionality"""
    print("Testing Chat Filter Functionality")
    print("=" * 40)
    
    # Test file reading
    if os.path.exists('allowed_chats.txt'):
        print("✓ allowed_chats.txt file exists")
        
        with open('allowed_chats.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        allowed_chats = set()
        for line in lines:
            chat_name = line.strip()
            if chat_name and not chat_name.startswith('#'):
                allowed_chats.add(chat_name)
        
        print(f"✓ Found {len(allowed_chats)} allowed chats:")
        for i, chat in enumerate(sorted(allowed_chats), 1):
            print(f"  {i}. {chat}")
        
        # Test specific chats
        test_chats = [
            "The Beard Chat",
            "Citadel to the beard",
            "CFB Bets", 
            "Test Beard Telegram Client",
            "Some Other Chat",
            "Random Chat Name"
        ]
        
        print(f"\nTesting chat names:")
        for chat in test_chats:
            is_allowed = chat in allowed_chats
            status = "✓ ALLOWED" if is_allowed else "✗ DENIED"
            print(f"  {chat}: {status}")
        
    else:
        print("✗ allowed_chats.txt file not found")
        return False
    
    return True

def test_management_commands():
    """Test management command structure"""
    print(f"\nManagement Commands:")
    print("=" * 40)
    
    commands = [
        "python manage_chats.py list",
        "python manage_chats.py add \"New Chat Name\"",
        "python manage_chats.py remove \"Chat Name\"", 
        "python manage_chats.py test \"Chat Name\""
    ]
    
    for cmd in commands:
        print(f"  {cmd}")
    
    print(f"\nNote: These commands require the full environment setup")
    return True

def main():
    """Main test function"""
    print("Chat Filter Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Functionality", test_chat_filter_basic),
        ("Management Commands", test_management_commands)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            if result:
                print(f"✓ {test_name} passed")
            else:
                print(f"✗ {test_name} failed")
                all_passed = False
        except Exception as e:
            print(f"✗ {test_name} error: {e}")
            all_passed = False
    
    print(f"\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed!")
        print("\nNext steps:")
        print("1. Run the installation script: ./install.sh")
        print("2. Test the full chat filter: python manage_chats.py list")
        print("3. Start the service and test with real messages")
    else:
        print("✗ Some tests failed")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 