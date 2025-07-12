import asyncio
import json
import time
import logging
import threading
from typing import Dict, Optional
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from config import Config, setup_logging, validate_config
from database import DatabaseManager
from webhook_client import WebhookClient
from chat_filter import ChatFilter

class TelegramClient:
    def __init__(self):
        self.logger = setup_logging()
        self.logger.info("Initializing Telegram Client")
        
        # Validate configuration
        validate_config()
        
        # Initialize components
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.db = DatabaseManager()
        self.webhook_client = WebhookClient()
        self.chat_filter = ChatFilter()
        
        # Application setup
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add message handler
        self.application.add_handler(
            MessageHandler(filters.ALL, self.handle_message)
        )
        
        # Processing state
        self.is_running = False
        self.processing_thread = None
        self.recovery_thread = None
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming Telegram messages"""
        try:
            message = update.message
            if not message:
                return
            
            # Get chat title for filtering
            chat_title = message.chat.title if message.chat else None
            
            # Check if this chat is allowed
            if not self.chat_filter.is_chat_allowed(chat_title):
                self.logger.debug(f"Ignoring message from non-allowed chat: '{chat_title}'")
                return
            
            # Extract message data
            message_data = {
                'message_id': str(message.message_id),
                'chat_id': str(message.chat_id),
                'chat_title': chat_title,
                'user_id': str(message.from_user.id) if message.from_user else None,
                'username': message.from_user.username if message.from_user else None,
                'text': message.text,
                'timestamp': message.date.isoformat(),
                'message_type': 'text',
                'raw_message': message.to_dict()
            }
            
            # Handle different message types
            if message.photo:
                message_data['message_type'] = 'photo'
                message_data['photo'] = [photo.file_id for photo in message.photo]
            elif message.document:
                message_data['message_type'] = 'document'
                message_data['document'] = message.document.file_id
            elif message.voice:
                message_data['message_type'] = 'voice'
                message_data['voice'] = message.voice.file_id
            elif message.video:
                message_data['message_type'] = 'video'
                message_data['video'] = message.video.file_id
            
            self.logger.info(f"Received message: {message_data['message_type']} from {message_data['username']}")
            
            # Try to send immediately, fallback to storage if failed
            success, response = self.webhook_client.send_message(message_data)
            
            if success:
                # Store as sent message
                self.db.store_sent_message(
                    message_data['message_id'],
                    message_data,
                    response
                )
                self.logger.info(f"Message {message_data['message_id']} sent successfully")
            else:
                # Store as pending message
                self.db.store_pending_message(message_data)
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
                                response
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
    
    def start(self):
        """Start the Telegram client"""
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
            
            # Start the bot
            self.logger.info("Starting Telegram bot polling")
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Error starting client: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the Telegram client"""
        self.logger.info("Stopping Telegram Client")
        self.is_running = False
        
        # Wait for threads to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
        
        if self.recovery_thread and self.recovery_thread.is_alive():
            self.recovery_thread.join(timeout=5)
        
        # Close database connection
        self.db.close()
        
        self.logger.info("Telegram Client stopped")

def main():
    """Main entry point"""
    client = TelegramClient()
    client.start()

if __name__ == "__main__":
    main() 