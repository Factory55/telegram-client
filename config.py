import os
from dotenv import load_dotenv
import logging

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Please ensure your .env file exists and is properly formatted.")

class Config:
    # Telegram Account Configuration
    TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
    TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE')
    TELEGRAM_PASSWORD = os.getenv('TELEGRAM_PASSWORD')  # 2FA password if enabled
    
    # Webhook Configuration
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    WEBHOOK_TIMEOUT = int(os.getenv('WEBHOOK_TIMEOUT', '30'))
    WEBHOOK_RETRY_ATTEMPTS = int(os.getenv('WEBHOOK_RETRY_ATTEMPTS', '3'))
    
    # Database Configuration
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')  # 'sqlite' or 'redis'
    SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'telegram_client.db')
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'telegram_client.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Recovery Configuration
    RECOVERY_CHECK_INTERVAL = int(os.getenv('RECOVERY_CHECK_INTERVAL', '60'))  # seconds
    MAX_QUEUE_SIZE = int(os.getenv('MAX_QUEUE_SIZE', '1000'))
    
    # Message Configuration
    MESSAGE_BATCH_SIZE = int(os.getenv('MESSAGE_BATCH_SIZE', '10'))
    MESSAGE_PROCESSING_INTERVAL = int(os.getenv('MESSAGE_PROCESSING_INTERVAL', '5'))  # seconds

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format=Config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_config():
    """Validate that all required environment variables are set"""
    required_vars = [
        'TELEGRAM_API_ID',
        'TELEGRAM_API_HASH',
        'TELEGRAM_PHONE',
        'WEBHOOK_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(Config, var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True 