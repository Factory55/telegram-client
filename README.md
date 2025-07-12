# Telegram Client for Raspberry Pi

A robust Telegram client designed to run on Raspberry Pi that forwards incoming messages as JSON to a webhook URL. Features include local caching, auto-recovery, comprehensive logging, and easy installation.

## Features

- **Message Forwarding**: Receives Telegram messages and forwards them as JSON to a configurable webhook URL
- **Local Caching**: Uses SQLite or Redis to cache messages when webhook is unavailable
- **Auto Recovery**: Automatically retries failed messages and recovers after power outages
- **Comprehensive Logging**: Detailed logging with configurable levels
- **Systemd Service**: Runs as a system service with auto-start on boot
- **Easy Installation**: Interactive installation script that configures all environment variables
- **Multiple Message Types**: Supports text, photos, documents, voice messages, and videos
- **Chat Filtering**: Only forwards messages from specified chat names
- **Dynamic Chat Management**: Add/remove allowed chats while the service is running

## Prerequisites

- Raspberry Pi (or any Linux system)
- Python 3.8 or higher
- Internet connection
- Telegram account with API credentials (from https://my.telegram.org/apps)
- Webhook URL to receive forwarded messages

## Quick Start

1. **Get Telegram API Credentials**:
   - Go to https://my.telegram.org/apps
   - Log in with your phone number
   - Create a new application
   - Note down your `api_id` and `api_hash`

2. **Clone the repository**:
   ```bash
   git clone https://github.com/Factory55/telegram-client.git
   cd telegram-client
   ```

3. **Run the installation script**:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **The script will prompt you for**:
   - Telegram API ID and Hash (from https://my.telegram.org/apps)
   - Your phone number
   - 2FA password (if enabled)
   - Webhook URL
   - Database preferences (SQLite/Redis)
   - Logging configuration
   - Performance settings

4. **Start the service**:
   ```bash
   sudo systemctl start telegram-client.service
   ```

5. **Check status**:
   ```bash
   ./status.sh
   ```

## Configuration

### Getting Telegram API Credentials

To use this client with your real Telegram account, you need to get API credentials:

1. **Visit Telegram API**: Go to https://my.telegram.org/apps
2. **Login**: Use your phone number to log in
3. **Create App**: Fill in the form with any app name and description
4. **Get Credentials**: Note down your `api_id` and `api_hash`
5. **Security**: Keep these credentials secure and don't share them

**Note**: This uses your real Telegram account, not a bot. The client will log in as you and forward messages from your chats.

### Environment Variables

The application uses a `.env` file for configuration. Key variables include:

#### Required
- `TELEGRAM_API_ID`: Your Telegram API ID from https://my.telegram.org/apps
- `TELEGRAM_API_HASH`: Your Telegram API Hash from https://my.telegram.org/apps
- `TELEGRAM_PHONE`: Your phone number (include country code)
- `WEBHOOK_URL`: The URL where messages will be forwarded as JSON

#### Optional
- `TELEGRAM_PASSWORD`: 2FA password (if enabled)
- `DATABASE_TYPE`: `sqlite` (default) or `redis`
- `WEBHOOK_TIMEOUT`: Request timeout in seconds (default: 30)
- `WEBHOOK_RETRY_ATTEMPTS`: Number of retry attempts (default: 3)
- `LOG_LEVEL`: Logging level (default: INFO)
- `MESSAGE_BATCH_SIZE`: Messages to process in batch (default: 10)
- `RECOVERY_CHECK_INTERVAL`: Recovery check interval in seconds (default: 60)

### Database Options

#### SQLite (Default)
- Lightweight, no additional setup required
- Stored in `telegram_client.db` file
- Suitable for most use cases

#### Redis
- Better performance for high message volumes
- Requires Redis server installation
- Configure with `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`

## Usage

### Service Management

```bash
# Start the service
sudo systemctl start telegram-client.service

# Stop the service
sudo systemctl stop telegram-client.service

# Restart the service
sudo systemctl restart telegram-client.service

# Check service status
sudo systemctl status telegram-client.service

# Enable auto-start on boot
sudo systemctl enable telegram-client.service
```

### Manual Scripts

```bash
# Manual start
./start.sh

# Check status and logs
./status.sh

# Stop service
./stop.sh

# Restart and show status
./restart.sh

# Manage allowed chats
./manage_chats.py list                    # List all allowed chats
./manage_chats.py add "My Chat Name"      # Add a chat to allowed list
./manage_chats.py remove "My Chat Name"   # Remove a chat from allowed list
./manage_chats.py test "My Chat Name"     # Test if a chat is allowed
```

### Logging

```bash
# View real-time logs
tail -f telegram_client.log

# View recent logs
tail -n 50 telegram_client.log

# View service logs
sudo journalctl -u telegram-client.service -f
```

## Message Format

Messages are forwarded to the webhook URL as JSON with the following structure:

```json
{
  "message_id": "12345",
  "chat_id": "67890",
  "user_id": "11111",
  "username": "user123",
  "text": "Hello world!",
  "timestamp": "2024-01-01T12:00:00",
  "message_type": "text",
  "raw_message": {
    // Complete Telegram message object
  }
}
```

### Message Types

- **text**: Plain text messages
- **photo**: Image messages (includes file_id array)
- **document**: File attachments (includes file_id)
- **voice**: Voice messages (includes file_id)
- **video**: Video messages (includes file_id)

### Chat Filtering

The client only forwards messages from chats listed in `allowed_chats.txt`. This file can be modified while the service is running, and changes are automatically detected within 5 seconds.

**File Format:**
```
# Add allowed chat names here (one per line)
# Lines starting with # are comments
The Beard Chat
Citadel to the beard 
CFB Bets
Test Beard Telegram Client
```

**Management Commands:**
```bash
# List all allowed chats
./manage_chats.py list

# Add a new chat
./manage_chats.py add "New Chat Name"

# Remove a chat
./manage_chats.py remove "Chat Name"

# Test if a chat is allowed
./manage_chats.py test "Chat Name"
```

## Architecture

### Components

1. **TelegramClient**: Main application that handles Telegram bot interactions
2. **DatabaseManager**: Manages message storage in SQLite or Redis
3. **WebhookClient**: Handles HTTP requests to the webhook URL
4. **Config**: Manages environment variables and configuration
5. **ChatFilter**: Filters messages based on allowed chat names

### Message Flow

1. Telegram message received
2. Check if chat is in allowed list
3. If not allowed: Ignore message
4. If allowed: Convert message to JSON format
5. Attempt to send to webhook URL
6. If successful: Store as sent message
7. If failed: Store as pending message
8. Background thread processes pending messages
9. Recovery monitor checks system health

### Recovery Features

- **Automatic Retry**: Failed messages are retried with exponential backoff
- **Power Outage Recovery**: Service automatically restarts and processes pending messages
- **Network Recovery**: Detects when webhook becomes available again
- **Database Persistence**: Messages survive system restarts

## Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   sudo systemctl status telegram-client.service
   tail -f telegram_client.log
   ```

2. **Messages not being forwarded**:
   - Check webhook URL is accessible
   - Verify API credentials and phone number
   - Check if 2FA password is correct (if enabled)
   - Check network connectivity

3. **Database errors**:
   - For SQLite: Check file permissions
   - For Redis: Verify Redis server is running

4. **High memory usage**:
   - Reduce `MESSAGE_BATCH_SIZE`
   - Increase `MESSAGE_PROCESSING_INTERVAL`
   - Consider using Redis instead of SQLite

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file:

```bash
# Edit .env file
nano .env

# Change LOG_LEVEL to DEBUG
LOG_LEVEL=DEBUG

# Restart service
sudo systemctl restart telegram-client.service
```

## Development

### Project Structure

```
telegram-client/
├── telegram_client.py    # Main application
├── config.py            # Configuration management
├── database.py          # Database operations
├── webhook_client.py    # HTTP client for webhooks
├── chat_filter.py       # Chat filtering logic
├── manage_chats.py      # Chat management script
├── allowed_chats.txt    # Allowed chat names
├── requirements.txt     # Python dependencies
├── install.sh          # Installation script
├── start.sh            # Manual start script
├── stop.sh             # Stop script
├── restart.sh          # Restart script
├── status.sh           # Status and monitoring script
├── .env                # Environment variables (created by install.sh)
├── telegram_client.db  # SQLite database (if using SQLite)
└── telegram_client.log # Application logs
```

### Adding New Message Types

To support new message types, modify the `handle_message` method in `telegram_client.py`:

```python
# Add new message type handling
elif message.new_message_type:
    message_data['message_type'] = 'new_message_type'
    message_data['new_message_type'] = message.new_message_type.file_id
```

## Security Considerations

- Keep your `.env` file secure (chmod 600)
- Use HTTPS for webhook URLs
- Regularly update dependencies
- Monitor logs for suspicious activity
- Consider using a firewall to restrict access

## License

This project is open source. Please check the license file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs: `tail -f telegram_client.log`
3. Check service status: `./status.sh`
4. Create an issue in the repository

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request