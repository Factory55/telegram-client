#!/usr/bin/env python3
"""
Telegram Authentication Setup Script

This script should be run interactively (not as a service) to set up
the initial authentication session for the Telegram client.

Usage:
    python auth_setup.py

After successful authentication, the session will be saved and the
main client can run headless as a service.
"""

import asyncio
import logging
from telethon import TelegramClient
from config import Config, setup_logging, validate_config

async def setup_authentication():
    """Set up Telegram authentication interactively"""
    logger = setup_logging()
    logger.info("Starting Telegram Authentication Setup")
    
    try:
        # Validate configuration
        validate_config()
        
        # Create client
        client = TelegramClient(
            'telegram_session',
            int(Config.TELEGRAM_API_ID),
            Config.TELEGRAM_API_HASH
        )
        
        logger.info("Starting authentication process...")
        logger.info(f"Phone number: {Config.TELEGRAM_PHONE}")
        
        # Start the client - this will prompt for verification code
        if Config.TELEGRAM_PASSWORD:
            logger.info("Using 2FA password from configuration")
            await client.start(phone=Config.TELEGRAM_PHONE, password=Config.TELEGRAM_PASSWORD)
        else:
            logger.info("Starting authentication (you may be prompted for verification code)")
            await client.start(phone=Config.TELEGRAM_PHONE)
        
        # Get user info to confirm successful login
        me = await client.get_me()
        logger.info(f"✅ Authentication successful!")
        logger.info(f"Logged in as: {me.first_name} (@{me.username})")
        logger.info(f"User ID: {me.id}")
        
        # Test connection
        logger.info("Testing connection...")
        await client.get_dialogs(limit=1)
        logger.info("✅ Connection test successful!")
        
        # Disconnect
        await client.disconnect()
        
        logger.info("✅ Authentication setup completed successfully!")
        logger.info("The session has been saved to 'telegram_session.session'")
        logger.info("You can now run the main client as a service.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Authentication setup failed: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("Telegram Authentication Setup")
    print("=" * 60)
    print()
    print("This script will help you authenticate with Telegram.")
    print("You may receive a verification code via SMS or Telegram app.")
    print()
    
    try:
        success = asyncio.run(setup_authentication())
        if success:
            print()
            print("🎉 Setup completed successfully!")
            print("You can now start the main service.")
        else:
            print()
            print("❌ Setup failed. Please check your configuration and try again.")
            return 1
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 