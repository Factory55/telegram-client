# Troubleshooting Guide

This guide helps you resolve common issues with the Telegram Client.

## Authentication Issues

### "EOF when reading a line" Error

**Problem**: The service fails to start with the error "EOF when reading a line"

**Cause**: This happens when the Telegram client tries to authenticate for the first time in a headless environment (like a systemd service) where there's no interactive terminal to input the verification code.

**Solution**:

1. **Stop the service**:
   ```bash
   sudo systemctl stop telegram-client.service
   ```

2. **Run authentication setup interactively**:
   ```bash
   python auth_setup.py
   ```

3. **Follow the prompts**:
   - Enter the verification code that Telegram sends to your phone
   - If you have 2FA enabled, enter your password when prompted
   - The script will create a session file (`telegram_session.session`)

4. **Restart the service**:
   ```bash
   sudo systemctl start telegram-client.service
   ```

5. **Check status**:
   ```bash
   ./status.sh
   ```

### Session Expired

**Problem**: The service was working but suddenly stopped working

**Cause**: Telegram sessions can expire, especially if you haven't used the account for a while

**Solution**:

1. **Delete the old session file**:
   ```bash
   rm telegram_session.session
   ```

2. **Run authentication setup again**:
   ```bash
   python auth_setup.py
   ```

3. **Restart the service**:
   ```bash
   sudo systemctl restart telegram-client.service
   ```

## Configuration Issues

### "Python-dotenv could not parse statement" Errors

**Problem**: Multiple errors about dotenv parsing

**Cause**: The `.env` file either doesn't exist or has formatting issues

**Solution**:

1. **Check if .env file exists**:
   ```bash
   ls -la .env
   ```

2. **If .env doesn't exist, create it**:
   ```bash
   python create_env.py
   ```

3. **Edit the .env file**:
   ```bash
   nano .env
   ```

4. **Ensure proper format**:
   - No spaces around the `=` sign
   - No quotes around values unless needed
   - One variable per line
   - No trailing spaces

   **Correct format**:
   ```
   TELEGRAM_API_ID=123456
   TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
   TELEGRAM_PHONE=+1234567890
   WEBHOOK_URL=https://your-webhook.com/webhook
   ```

   **Incorrect format**:
   ```
   TELEGRAM_API_ID = 123456
   TELEGRAM_API_HASH="abcdef1234567890abcdef1234567890"
   TELEGRAM_PHONE= +1234567890 
   ```

### Missing Environment Variables

**Problem**: "Missing required environment variables" error

**Solution**:

1. **Check your .env file**:
   ```bash
   cat .env
   ```

2. **Verify all required variables are set**:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELEGRAM_PHONE`
   - `WEBHOOK_URL`

3. **If any are missing, add them to .env**:
   ```bash
   nano .env
   ```

## Service Issues

### Service Won't Start

**Problem**: `sudo systemctl start telegram-client.service` fails

**Diagnosis**:
```bash
sudo systemctl status telegram-client.service
sudo journalctl -u telegram-client.service -n 50
```

**Common Solutions**:

1. **Check file permissions**:
   ```bash
   ls -la telegram_client.py
   chmod +x telegram_client.py
   ```

2. **Check Python virtual environment**:
   ```bash
   ls -la venv/bin/python
   ```

3. **Check working directory**:
   ```bash
   sudo systemctl show telegram-client.service | grep WorkingDirectory
   ```

4. **Test manual start**:
   ```bash
   ./start.sh
   ```

### Service Keeps Restarting

**Problem**: Service starts but immediately stops and restarts

**Diagnosis**:
```bash
sudo journalctl -u telegram-client.service -f
```

**Common Causes**:
- Authentication issues (most common)
- Missing .env file
- Invalid configuration values
- Permission issues

## Network Issues

### Webhook Not Reachable

**Problem**: Messages are stored as pending but not sent

**Diagnosis**:
```bash
curl -X POST https://your-webhook-url.com/webhook -H "Content-Type: application/json" -d '{"test": "message"}'
```

**Solutions**:
- Check webhook URL is correct
- Verify webhook server is running
- Check firewall settings
- Test with a simple webhook service (like webhook.site)

### Telegram Connection Issues

**Problem**: Can't connect to Telegram servers

**Diagnosis**:
```bash
ping api.telegram.org
```

**Solutions**:
- Check internet connection
- Verify firewall allows outbound HTTPS
- Check if Telegram is blocked in your region

## Database Issues

### SQLite Permission Errors

**Problem**: "Permission denied" when accessing database

**Solution**:
```bash
sudo chown $USER:$USER telegram_client.db
chmod 644 telegram_client.db
```

### Redis Connection Issues

**Problem**: Can't connect to Redis

**Diagnosis**:
```bash
redis-cli ping
```

**Solutions**:
- Start Redis service: `sudo systemctl start redis`
- Check Redis configuration
- Verify Redis credentials in .env

## Log Analysis

### Enable Debug Logging

To get more detailed logs:

1. **Edit .env file**:
   ```bash
   nano .env
   ```

2. **Change log level**:
   ```
   LOG_LEVEL=DEBUG
   ```

3. **Restart service**:
   ```bash
   sudo systemctl restart telegram-client.service
   ```

4. **View logs**:
   ```bash
   tail -f telegram_client.log
   ```

### Common Log Messages

- `"Logged in as: ..."` - Authentication successful
- `"Message ... sent successfully"` - Webhook delivery successful
- `"Message ... stored as pending"` - Webhook delivery failed
- `"Ignoring message from non-allowed chat"` - Chat filtering working
- `"Processing ... pending messages"` - Recovery system working

## Quick Fixes

### Complete Reset

If nothing else works, try a complete reset:

1. **Stop service**:
   ```bash
   sudo systemctl stop telegram-client.service
   ```

2. **Remove session and database**:
   ```bash
   rm -f telegram_session.session telegram_client.db
   ```

3. **Recreate .env**:
   ```bash
   rm .env
   python create_env.py
   nano .env  # Add your values
   ```

4. **Run authentication**:
   ```bash
   python auth_setup.py
   ```

5. **Start service**:
   ```bash
   sudo systemctl start telegram-client.service
   ```

### Emergency Mode

If you need the service running immediately:

1. **Use test mode**:
   ```bash
   python test_setup.py
   ```

2. **Check if basic connectivity works**:
   ```bash
   python -c "from config import Config; print('Config loaded:', bool(Config.TELEGRAM_API_ID))"
   ```

## Getting Help

If you're still having issues:

1. **Collect diagnostic information**:
   ```bash
   ./status.sh > diagnostic.txt 2>&1
   sudo journalctl -u telegram-client.service > service_logs.txt
   ```

2. **Check the logs**:
   ```bash
   tail -n 100 telegram_client.log
   ```

3. **Verify your setup**:
   ```bash
   python test_setup.py
   ```

4. **Create an issue** with:
   - Your error messages
   - The diagnostic output
   - Your .env file (with sensitive data redacted)
   - Steps to reproduce the issue 