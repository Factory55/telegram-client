#!/bin/bash

# Telegram Client Installation Script
# This script sets up the Telegram client on a Raspberry Pi

set -e

echo "=========================================="
echo "Telegram Client Installation Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    print_warning "This script is designed for Raspberry Pi, but you can continue anyway."
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

print_status "Python version check passed: $python_version"

# Update system packages
print_header "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
print_header "Installing system dependencies..."
sudo apt-get install -y python3-pip python3-venv git curl wget

# Create virtual environment
print_header "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
print_header "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file
print_header "Setting up environment variables..."
echo "Please provide the following information:"
echo ""

# Function to prompt for input with validation
prompt_input() {
    local var_name=$1
    local prompt_text=$2
    local is_required=$3
    local default_value=$4
    
    while true; do
        if [ -n "$default_value" ]; then
            read -p "$prompt_text [$default_value]: " input_value
            input_value=${input_value:-$default_value}
        else
            read -p "$prompt_text: " input_value
        fi
        
        if [ "$is_required" = "true" ] && [ -z "$input_value" ]; then
            print_error "This field is required!"
            continue
        fi
        
        break
    done
    
    echo "$var_name=$input_value" >> .env
}

# Required environment variables
prompt_input "TELEGRAM_BOT_TOKEN" "Enter your Telegram Bot Token (from @BotFather)" "true"
prompt_input "TELEGRAM_CHAT_ID" "Enter your Telegram Chat ID (where messages will be sent)" "true"
prompt_input "WEBHOOK_URL" "Enter the webhook URL where messages will be forwarded" "true"

echo ""
print_header "Optional Configuration:"
echo ""

# Optional environment variables
prompt_input "WEBHOOK_TIMEOUT" "Webhook request timeout (seconds)" "false" "30"
prompt_input "WEBHOOK_RETRY_ATTEMPTS" "Number of retry attempts for failed webhooks" "false" "3"

echo ""
print_header "Database Configuration:"
echo ""

prompt_input "DATABASE_TYPE" "Database type (sqlite/redis)" "false" "sqlite"
prompt_input "SQLITE_DB_PATH" "SQLite database file path" "false" "telegram_client.db"

echo ""
print_header "Redis Configuration (if using Redis):"
echo ""

prompt_input "REDIS_HOST" "Redis host" "false" "localhost"
prompt_input "REDIS_PORT" "Redis port" "false" "6379"
prompt_input "REDIS_DB" "Redis database number" "false" "0"
prompt_input "REDIS_PASSWORD" "Redis password (leave empty if none)" "false" ""

echo ""
print_header "Logging Configuration:"
echo ""

prompt_input "LOG_LEVEL" "Log level (DEBUG/INFO/WARNING/ERROR)" "false" "INFO"
prompt_input "LOG_FILE" "Log file path" "false" "telegram_client.log"

echo ""
print_header "Performance Configuration:"
echo ""

prompt_input "RECOVERY_CHECK_INTERVAL" "Recovery check interval (seconds)" "false" "60"
prompt_input "MAX_QUEUE_SIZE" "Maximum queue size for pending messages" "false" "1000"
prompt_input "MESSAGE_BATCH_SIZE" "Number of messages to process in batch" "false" "10"
prompt_input "MESSAGE_PROCESSING_INTERVAL" "Message processing interval (seconds)" "false" "5"

# Create systemd service file
print_header "Creating systemd service..."
sudo tee /etc/systemd/system/telegram-client.service > /dev/null <<EOF
[Unit]
Description=Telegram Client Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python telegram_client.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
print_header "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable telegram-client.service

# Create log directory
mkdir -p logs

# Set proper permissions
chmod +x telegram_client.py
chmod 600 .env

# Create startup script
print_header "Creating startup script..."
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python telegram_client.py
EOF

chmod +x start.sh

# Create status script
print_header "Creating status script..."
cat > status.sh << 'EOF'
#!/bin/bash
echo "=== Telegram Client Status ==="
echo "Service Status:"
sudo systemctl status telegram-client.service --no-pager -l
echo ""
echo "Recent Logs:"
tail -n 20 telegram_client.log
echo ""
echo "Database Stats:"
python -c "
import sys
sys.path.append('.')
from database import DatabaseManager
from config import setup_logging
setup_logging()
db = DatabaseManager()
stats = db.get_stats()
print(f'Pending messages: {stats.get(\"pending_count\", 0)}')
print(f'Sent messages: {stats.get(\"sent_count\", 0)}')
print(f'Database type: {stats.get(\"database_type\", \"unknown\")}')
db.close()
"
echo ""
echo "Chat Filter Stats:"
python -c "
import sys
sys.path.append('.')
from chat_filter import ChatFilter
from config import setup_logging
setup_logging()
chat_filter = ChatFilter()
stats = chat_filter.get_stats()
print(f'Allowed chats: {stats.get(\"allowed_chats_count\", 0)}')
if stats.get('allowed_chats'):
    print('Allowed chat names:')
    for chat in stats['allowed_chats']:
        print(f'  - {chat}')
"
EOF

chmod +x status.sh

# Create stop script
print_header "Creating stop script..."
cat > stop.sh << 'EOF'
#!/bin/bash
sudo systemctl stop telegram-client.service
echo "Telegram client stopped"
EOF

chmod +x stop.sh

# Create restart script
print_header "Creating restart script..."
cat > restart.sh << 'EOF'
#!/bin/bash
sudo systemctl restart telegram-client.service
echo "Telegram client restarted"
sleep 2
./status.sh
EOF

chmod +x restart.sh

print_header "Installation Complete!"
echo ""
print_status "Files created:"
echo "  - .env (environment variables)"
echo "  - start.sh (manual start script)"
echo "  - stop.sh (stop script)"
echo "  - restart.sh (restart script)"
echo "  - status.sh (status and logs)"
echo ""
print_status "Service created: telegram-client.service"
echo ""
print_status "To start the service:"
echo "  sudo systemctl start telegram-client.service"
echo ""
print_status "To check status:"
echo "  ./status.sh"
echo ""
print_status "To view logs:"
echo "  tail -f telegram_client.log"
echo ""
print_status "To stop the service:"
echo "  sudo systemctl stop telegram-client.service"
echo ""
print_warning "The service will automatically start on boot."
print_warning "Make sure your .env file is properly configured before starting."
echo ""
print_header "Next steps:"
echo "1. Verify your .env configuration"
echo "2. Start the service: sudo systemctl start telegram-client.service"
echo "3. Check status: ./status.sh"
echo "4. Send a test message to your Telegram bot"
echo ""

# Ask if user wants to start the service now
read -p "Do you want to start the service now? (y/n): " start_now
if [[ $start_now =~ ^[Yy]$ ]]; then
    print_status "Starting Telegram client service..."
    sudo systemctl start telegram-client.service
    sleep 3
    ./status.sh
fi

print_status "Installation completed successfully!" 