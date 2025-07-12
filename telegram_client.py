import asyncio
import json
import time
import logging
import threading
import os
from typing import Dict, Optional
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import User, Chat, Channel
from config import Config, setup_logging, validate_config
from database import DatabaseManager
from webhook_client import WebhookClient
# from chat_filter import ChatFilter  # Chat filtering disabled

class TelegramClientApp:
    def __init__(self):
        self.logger = setup_logging()
        self.logger.info("Initializing Telegram Client")
        
        # Validate configuration
        validate_config()
        
        # Initialize components
        self.client = TelegramClient(
            'telegram_session',
            int(Config.TELEGRAM_API_ID),
            Config.TELEGRAM_API_HASH
        )
        self.db = DatabaseManager()
        self.webhook_client = WebhookClient()
        # self.chat_filter = ChatFilter()  # Chat filtering disabled
        
        # Processing state
        self.is_running = False
        self.processing_thread = None
        self.recovery_thread = None
    
    def serialize_message_data(self, message_data: Dict) -> Dict:
        """
        Serialize message data to ensure it's JSON-compatible
        Converts datetime objects to ISO format strings
        """
        def serialize_value(value):
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [serialize_value(v) for v in value]
            else:
                return value
        
        return serialize_value(message_data)  # type: ignore
        
    async def start_client(self):
        """Start the Telegram client and authenticate"""
        try:
            # Check if session file exists
            session_exists = os.path.exists('telegram_session.session')
            
            if not session_exists:
                self.logger.info("No session file found. First-time authentication required.")
                self.logger.info("Please run the client interactively first to authenticate:")
                self.logger.info("python telegram_client.py")
                self.logger.info("After authentication, the session will be saved and the service can run headless.")
                return False
            
            # Start the client with proper 2FA handling
            if Config.TELEGRAM_PASSWORD:
                # If 2FA password is provided in config, use it
                await self.client.start(phone=Config.TELEGRAM_PHONE, password=Config.TELEGRAM_PASSWORD)
            else:
                # Try to start with existing session
                await self.client.start(phone=Config.TELEGRAM_PHONE)
            
            # Get user info
            me = await self.client.get_me()
            self.logger.info(f"Logged in as: {me.first_name} (@{me.username})")
            
            # Set up message handler
            @self.client.on(events.NewMessage)
            async def handle_new_message(event):
                await self.handle_message(event)
            
            self.logger.info("Telegram client started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Telegram client: {e}")
            return False
    
    async def handle_message(self, event):
        """Handle incoming Telegram messages"""
        try:
            message = event.message
            chat = await event.get_chat()
            
            # Get chat title for filtering
            chat_title = None
            if hasattr(chat, 'title'):
                chat_title = chat.title
            elif hasattr(chat, 'first_name'):
                chat_title = f"{chat.first_name} {chat.last_name or ''}".strip()
            
            # Chat filtering disabled - allowing all messages through
            # if not self.chat_filter.is_chat_allowed(chat_title):
            #     self.logger.debug(f"Ignoring message from non-allowed chat: '{chat_title}'")
            #     return
            
            # Get sender info
            sender = await event.get_sender()
            sender_name = None
            sender_username = None
            
            if sender:
                if hasattr(sender, 'first_name'):
                    sender_name = f"{sender.first_name} {sender.last_name or ''}".strip()
                if hasattr(sender, 'username'):
                    sender_username = sender.username
            
            # Extract message data
            message_data = {
                'message_id': str(message.id),
                'chat_id': str(chat.id),
                'chat_title': chat_title,
                'user_id': str(sender.id) if sender else None,
                'username': sender_username,
                'sender_name': sender_name,
                'text': message.text,
                'timestamp': message.date.isoformat(),
                'message_type': 'text'
            }
            
            # Handle different message types
            if message.media:
                if hasattr(message.media, 'photo'):
                    message_data['message_type'] = 'photo'
                    message_data['photo'] = True
                elif hasattr(message.media, 'document'):
                    message_data['message_type'] = 'document'
                    message_data['document'] = True
                elif hasattr(message.media, 'voice'):
                    message_data['message_type'] = 'voice'
                    message_data['voice'] = True
                elif hasattr(message.media, 'video'):
                    message_data['message_type'] = 'video'
                    message_data['video'] = True
            
            self.logger.info(f"Received message: {message_data['message_type']} from {sender_name or sender_username} in {chat_title}")
            
            # Serialize message data to ensure JSON compatibility
            serialized_data = self.serialize_message_data(message_data)
            
            # Try to send immediately, fallback to storage if failed
            success, response = self.webhook_client.send_message(serialized_data)
            
            if success:
                # Store as sent message
                self.db.store_sent_message(
                    message_data['message_id'],
                    serialized_data,
                    response or ""
                )
                self.logger.info(f"Message {message_data['message_id']} sent successfully")
            else:
                # Store as pending message
                self.db.store_pending_message(serialized_data)
                self.logger.warning(f"Message {message_data['message_id']} stored as pending: {response}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    def process_pending_messages(self):
        """Process pending messages in background thread"""
        while self.is_running:
            try:
                # Get pending messages
                pending_messages = self.db.get_pending_messages(Config.MESSAGE_BATCH_SIZE)
                
                if not pending_messages:
                    time.sleep(Config.MESSAGE_PROCESSING_INTERVAL)
                    continue
                
                self.logger.info(f"Processing {len(pending_messages)} pending messages")
                
                for message in pending_messages:
                    if not self.is_running:
                        break
                    
                    try:
                        # Try to send the message
                        success, response = self.webhook_client.send_message(message['message_data'])
                        
                        if success:
                            # Remove from pending and store as sent
                            self.db.remove_pending_message(message['id'])
                            self.db.store_sent_message(
                                message['message_data']['message_id'],
                                message['message_data'],
                                response or ""
                            )
                            self.logger.info(f"Pending message {message['id']} sent successfully")
                        else:
                            # Update retry count
                            new_retry_count = message['retry_count'] + 1
                            self.db.update_retry_count(message['id'], new_retry_count)
                            
                            if new_retry_count >= Config.WEBHOOK_RETRY_ATTEMPTS:
                                self.logger.error(f"Message {message['id']} exceeded max retries")
                            else:
                                self.logger.warning(f"Message {message['id']} retry {new_retry_count}: {response}")
                    
                    except Exception as e:
                        self.logger.error(f"Error processing pending message {message['id']}: {e}")
                
                time.sleep(Config.MESSAGE_PROCESSING_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Error in pending message processing: {e}")
                time.sleep(Config.MESSAGE_PROCESSING_INTERVAL)
    
    def recovery_monitor(self):
        """Monitor for recovery scenarios (power outage, network issues)"""
        while self.is_running:
            try:
                # Check if webhook is reachable
                if not self.webhook_client.test_connection():
                    self.logger.warning("Webhook not reachable, will retry pending messages")
                
                # Log statistics
                stats = self.db.get_stats()
                self.logger.info(f"Database stats: {stats}")
                
                time.sleep(Config.RECOVERY_CHECK_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Error in recovery monitor: {e}")
                time.sleep(Config.RECOVERY_CHECK_INTERVAL)
    
    async def run(self):
        """Run the Telegram client"""
        try:
            self.logger.info("Starting Telegram Client")
            self.is_running = True
            
            # Start background threads
            self.processing_thread = threading.Thread(
                target=self.process_pending_messages,
                daemon=True
            )
            self.processing_thread.start()
            
            self.recovery_thread = threading.Thread(
                target=self.recovery_monitor,
                daemon=True
            )
            self.recovery_thread.start()
            
            # Start the Telegram client
            if await self.start_client():
                self.logger.info("Telegram client running. Press Ctrl+C to stop.")
                await self.client.run_until_disconnected()
            else:
                self.logger.error("Failed to start Telegram client")
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Error running client: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the Telegram client"""
        self.logger.info("Stopping Telegram Client")
        self.is_running = False
        
        # Wait for threads to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
        
        if self.recovery_thread and self.recovery_thread.is_alive():
            self.recovery_thread.join(timeout=5)
        
        # Disconnect Telegram client
        if self.client:
            await self.client.disconnect()
        
        # Close database connection
        self.db.close()
        
        self.logger.info("Telegram Client stopped")

def main():
    """Main entry point"""
    try:
        client = TelegramClientApp()
        asyncio.run(client.run())
    except Exception as e:
        print(f"Error: {e}")
        print("\nIf you're seeing authentication errors, please run the setup script first:")
        print("python auth_setup.py")
        return 1
    return 0

if __name__ == "__main__":
    exit(main()) 