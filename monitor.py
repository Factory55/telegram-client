#!/usr/bin/env python3
"""
Monitoring script for Telegram Client
"""

import os
import sys
import time
import json
import psutil
from datetime import datetime
from typing import Dict, Any

def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'uptime': time.time() - psutil.boot_time()
    }

def get_service_status() -> Dict[str, Any]:
    """Get systemd service status"""
    try:
        import subprocess
        result = subprocess.run(
            ['systemctl', 'is-active', 'telegram-client.service'],
            capture_output=True,
            text=True
        )
        is_active = result.stdout.strip() == 'active'
        
        # Get service uptime
        if is_active:
            result = subprocess.run(
                ['systemctl', 'show', 'telegram-client.service', '--property=ActiveEnterTimestamp'],
                capture_output=True,
                text=True
            )
            timestamp = result.stdout.strip().split('=')[1] if '=' in result.stdout else 'Unknown'
        else:
            timestamp = 'Not running'
        
        return {
            'is_active': is_active,
            'start_time': timestamp
        }
    except Exception as e:
        return {
            'is_active': False,
            'error': str(e)
        }

def get_log_stats() -> Dict[str, Any]:
    """Get log file statistics"""
    log_file = 'telegram_client.log'
    
    if not os.path.exists(log_file):
        return {'exists': False}
    
    try:
        stat = os.stat(log_file)
        size_mb = stat.st_size / (1024 * 1024)
        
        # Count recent log entries
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = [line for line in lines[-100:] if line.strip()]
            
            error_count = len([line for line in recent_lines if 'ERROR' in line])
            warning_count = len([line for line in recent_lines if 'WARNING' in line])
            info_count = len([line for line in recent_lines if 'INFO' in line])
        
        return {
            'exists': True,
            'size_mb': round(size_mb, 2),
            'total_lines': len(lines),
            'recent_errors': error_count,
            'recent_warnings': warning_count,
            'recent_info': info_count,
            'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    except Exception as e:
        return {
            'exists': True,
            'error': str(e)
        }

def get_database_stats() -> Dict[str, Any]:
    """Get database statistics"""
    try:
        from database import DatabaseManager
        from config import setup_logging
        
        setup_logging()
        db = DatabaseManager()
        stats = db.get_stats()
        db.close()
        
        return stats
    except Exception as e:
        return {'error': str(e)}

def get_chat_filter_stats() -> Dict[str, Any]:
    """Get chat filter statistics"""
    try:
        from chat_filter import ChatFilter
        from config import setup_logging
        
        setup_logging()
        chat_filter = ChatFilter()
        stats = chat_filter.get_stats()
        
        return stats
    except Exception as e:
        return {'error': str(e)}

def format_uptime(seconds: float) -> str:
    """Format uptime in human readable format"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def print_status():
    """Print comprehensive status information"""
    print("=" * 60)
    print("Telegram Client Status Monitor")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # System information
    print("📊 System Information:")
    print("-" * 30)
    sys_info = get_system_info()
    print(f"CPU Usage: {sys_info['cpu_percent']}%")
    print(f"Memory Usage: {sys_info['memory_percent']}%")
    print(f"Disk Usage: {sys_info['disk_percent']}%")
    print(f"System Uptime: {format_uptime(sys_info['uptime'])}")
    print()
    
    # Service status
    print("🔧 Service Status:")
    print("-" * 30)
    service_status = get_service_status()
    if service_status['is_active']:
        print("✓ Service is running")
        print(f"  Started: {service_status['start_time']}")
    else:
        print("✗ Service is not running")
        if 'error' in service_status:
            print(f"  Error: {service_status['error']}")
    print()
    
    # Log statistics
    print("📝 Log Statistics:")
    print("-" * 30)
    log_stats = get_log_stats()
    if log_stats['exists']:
        if 'error' in log_stats:
            print(f"✗ Error reading log: {log_stats['error']}")
        else:
            print(f"Log file size: {log_stats['size_mb']} MB")
            print(f"Total log lines: {log_stats['total_lines']}")
            print(f"Recent errors: {log_stats['recent_errors']}")
            print(f"Recent warnings: {log_stats['recent_warnings']}")
            print(f"Recent info: {log_stats['recent_info']}")
            print(f"Last modified: {log_stats['last_modified']}")
    else:
        print("✗ Log file not found")
    print()
    
    # Database statistics
    print("🗄️  Database Statistics:")
    print("-" * 30)
    db_stats = get_database_stats()
    if 'error' in db_stats:
        print(f"✗ Error reading database: {db_stats['error']}")
    else:
        print(f"Database type: {db_stats.get('database_type', 'Unknown')}")
        print(f"Pending messages: {db_stats.get('pending_count', 0)}")
        print(f"Sent messages: {db_stats.get('sent_count', 0)}")
    print()
    
    # Chat filter statistics
    print("🔒 Chat Filter Statistics:")
    print("-" * 30)
    chat_filter_stats = get_chat_filter_stats()
    if 'error' in chat_filter_stats:
        print(f"✗ Error reading chat filter: {chat_filter_stats['error']}")
    else:
        print(f"Allowed chats: {chat_filter_stats.get('allowed_chats_count', 0)}")
        if chat_filter_stats.get('allowed_chats'):
            print("Allowed chat names:")
            for chat in chat_filter_stats['allowed_chats']:
                print(f"  - {chat}")
        print(f"File: {chat_filter_stats.get('file_path', 'Unknown')}")
    print()
    
    # Recent log entries
    print("📋 Recent Log Entries:")
    print("-" * 30)
    log_file = 'telegram_client.log'
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-10:]  # Last 10 lines
                for line in recent_lines:
                    line = line.strip()
                    if line:
                        # Truncate long lines
                        if len(line) > 100:
                            line = line[:97] + "..."
                        print(line)
        except Exception as e:
            print(f"Error reading log file: {e}")
    else:
        print("No log file found")
    
    print("=" * 60)

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--watch':
        # Continuous monitoring mode
        print("Starting continuous monitoring (Ctrl+C to stop)...")
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                print_status()
                time.sleep(30)  # Update every 30 seconds
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    else:
        # Single status check
        print_status()

if __name__ == "__main__":
    main() 