import requests
import json
import time
import logging
from typing import Dict, Optional
from config import Config

class WebhookClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.webhook_url = Config.WEBHOOK_URL
        self.timeout = Config.WEBHOOK_TIMEOUT
        self.max_retries = Config.WEBHOOK_RETRY_ATTEMPTS
    
    def send_message(self, message_data: Dict) -> tuple[bool, Optional[str]]:
        """
        Send message to webhook URL
        
        Returns:
            tuple: (success: bool, response_text: Optional[str])
        """
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramClient/1.0'
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"Sending message to webhook (attempt {attempt + 1}/{self.max_retries + 1})")
                
                response = requests.post(
                    self.webhook_url,
                    json=message_data,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    self.logger.info("Message sent successfully to webhook")
                    return True, response.text
                else:
                    self.logger.warning(
                        f"Webhook returned status {response.status_code}: {response.text}"
                    )
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        return False, f"HTTP {response.status_code}: {response.text}"
                        
            except requests.exceptions.Timeout:
                self.logger.warning(f"Webhook request timed out (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return False, "Request timeout"
                    
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"Connection error to webhook (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return False, f"Connection error: {str(e)}"
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error to webhook (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return False, f"Request error: {str(e)}"
        
        return False, "Max retries exceeded"
    
    def test_connection(self) -> bool:
        """Test if the webhook URL is reachable"""
        try:
            response = requests.get(
                self.webhook_url,
                timeout=10,
                headers={'User-Agent': 'TelegramClient/1.0'}
            )
            self.logger.info(f"Webhook connection test successful: {response.status_code}")
            return True
        except Exception as e:
            self.logger.error(f"Webhook connection test failed: {e}")
            return False 