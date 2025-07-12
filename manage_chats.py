#!/usr/bin/env python3
"""
Chat Filter Management Script
"""

import sys
import argparse
from chat_filter import ChatFilter
from config import setup_logging

def list_chats(chat_filter: ChatFilter):
    """List all allowed chats"""
    stats = chat_filter.get_stats()
    print(f"\n📋 Allowed Chats ({stats['allowed_chats_count']} total):")
    print("-" * 40)
    
    if stats['allowed_chats']:
        for i, chat in enumerate(stats['allowed_chats'], 1):
            print(f"{i:2d}. {chat}")
    else:
        print("No allowed chats configured")
    
    print(f"\nFile: {stats['file_path']}")

def add_chat(chat_filter: ChatFilter, chat_name: str):
    """Add a chat to the allowed list"""
    print(f"\n➕ Adding chat: '{chat_name}'")
    
    if chat_filter.add_allowed_chat(chat_name):
        print("✓ Chat added successfully")
        print("Note: Changes will be picked up automatically within 5 seconds")
    else:
        print("✗ Failed to add chat")
        sys.exit(1)

def remove_chat(chat_filter: ChatFilter, chat_name: str):
    """Remove a chat from the allowed list"""
    print(f"\n➖ Removing chat: '{chat_name}'")
    
    if chat_filter.remove_allowed_chat(chat_name):
        print("✓ Chat removed successfully")
        print("Note: Changes will be picked up automatically within 5 seconds")
    else:
        print("✗ Failed to remove chat (may not exist)")
        sys.exit(1)

def test_chat(chat_filter: ChatFilter, chat_name: str):
    """Test if a chat is allowed"""
    print(f"\n🔍 Testing chat: '{chat_name}'")
    
    is_allowed = chat_filter.is_chat_allowed(chat_name)
    if is_allowed:
        print("✓ Chat is allowed")
    else:
        print("✗ Chat is not allowed")
        print("\nCurrent allowed chats:")
        stats = chat_filter.get_stats()
        for chat in stats['allowed_chats']:
            print(f"  - {chat}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Manage allowed chats for Telegram client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                    # List all allowed chats
  %(prog)s add "My Chat Name"      # Add a chat to allowed list
  %(prog)s remove "My Chat Name"   # Remove a chat from allowed list
  %(prog)s test "My Chat Name"     # Test if a chat is allowed
        """
    )
    
    parser.add_argument(
        'action',
        choices=['list', 'add', 'remove', 'test'],
        help='Action to perform'
    )
    
    parser.add_argument(
        'chat_name',
        nargs='?',
        help='Chat name for add/remove/test actions'
    )
    
    parser.add_argument(
        '--file',
        default='allowed_chats.txt',
        help='Path to allowed chats file (default: allowed_chats.txt)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.action in ['add', 'remove', 'test'] and not args.chat_name:
        parser.error(f"Action '{args.action}' requires a chat name")
    
    # Setup logging
    setup_logging()
    
    try:
        # Initialize chat filter
        chat_filter = ChatFilter(args.file)
        
        # Perform action
        if args.action == 'list':
            list_chats(chat_filter)
        elif args.action == 'add':
            add_chat(chat_filter, args.chat_name)
        elif args.action == 'remove':
            remove_chat(chat_filter, args.chat_name)
        elif args.action == 'test':
            test_chat(chat_filter, args.chat_name)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 