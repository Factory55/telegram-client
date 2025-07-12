# Telegram API Setup Guide

This guide will help you get the API credentials needed to use your real Telegram account with this client.

## Step 1: Visit Telegram API Website

1. Open your web browser
2. Go to: https://my.telegram.org/apps
3. You'll see a login page

## Step 2: Login with Your Phone Number

1. Enter your phone number (include country code)
2. Click "Next"
3. You'll receive a Telegram message with a code
4. Enter the code on the website
5. Click "Sign In"

## Step 3: Create a New Application

1. You'll see a form to create a new application
2. Fill in the following fields:
   - **App title**: Any name you want (e.g., "My Telegram Client")
   - **Short name**: A short version (e.g., "myclient")
   - **URL**: Can be left empty or use "https://example.com"
   - **Platform**: Choose "Desktop"
   - **Description**: Brief description (e.g., "Personal Telegram client")

3. Click "Create application"

## Step 4: Get Your Credentials

After creating the application, you'll see:
- **api_id**: A number (e.g., 12345678)
- **api_hash**: A long string of letters and numbers

**Important**: Save both of these values securely!

## Step 5: Use in Installation

When running the installation script, you'll be prompted for:
- **TELEGRAM_API_ID**: Enter the api_id number
- **TELEGRAM_API_HASH**: Enter the api_hash string
- **TELEGRAM_PHONE**: Your phone number with country code (e.g., +1234567890)
- **TELEGRAM_PASSWORD**: Your 2FA password (required if you have 2FA enabled, leave empty if not)

## Step 6: First Login Process

When you start the client for the first time:

1. **Telegram will send you a login code** via Telegram message
2. **Enter the code in the terminal** when prompted
3. **If you have 2FA enabled**:
   - If you provided the 2FA password in the config → automatic login
   - If you left it blank → you'll be prompted to enter it in the terminal
4. **A session file will be created** (`telegram_session.session`) to remember your login
5. **Future starts will be automatic** - no more code entry needed

**Note**: The login code is sent to your Telegram account, not via SMS. Check your Telegram app for the message.

## Security Notes

- Keep your API credentials secure
- Don't share them with anyone
- The session file will be created locally and contains your login session
- You can revoke access by going back to https://my.telegram.org/apps

## Troubleshooting

**"Phone number invalid"**
- Make sure to include the country code (e.g., +1 for US, +44 for UK)

**"API credentials invalid"**
- Double-check your api_id and api_hash
- Make sure you copied them exactly from the website

**"2FA password required"**
- If you have 2FA enabled, you have two options:
  - **Option 1**: Provide the 2FA password in the config for automatic login
  - **Option 2**: Leave it blank and enter it manually when prompted
- This is the password you set up for Telegram's two-factor authentication
- If you leave it blank and have 2FA enabled, you'll be prompted to enter it in the terminal

**"Session expired"**
- Delete the `telegram_session.session` file
- Run the client again to re-authenticate

**"Login code required"**
- Check your Telegram app for the login code message
- Enter the code in the terminal when prompted
- The code is sent to your Telegram account, not via SMS

## Example Configuration

Your `.env` file should look like this:
```
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+1234567890
TELEGRAM_PASSWORD=your_2fa_password_here
WEBHOOK_URL=https://your-webhook-url.com/webhook
```

## What This Means

- The client will log in as **you** (your real Telegram account)
- It will forward messages from your chats to the webhook
- Only messages from allowed chats (in `allowed_chats.txt`) will be forwarded
- Your session is stored locally and will persist between restarts 