import sqlite3
import json
import time
import logging
from typing import List, Dict, Optional
from config import Config

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available, falling back to SQLite")

class DatabaseManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_type = Config.DATABASE_TYPE
        
        if self.db_type == 'redis' and REDIS_AVAILABLE:
            self._init_redis()
        else:
            self._init_sqlite()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD,
                decode_responses=True
            )
            self.redis_client.ping()
            self.logger.info("Connected to Redis database")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            self.logger.info("Falling back to SQLite")
            self.db_type = 'sqlite'
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Initialize SQLite database"""
        try:
            self.conn = sqlite3.connect(Config.SQLITE_DB_PATH, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
            self.logger.info("Connected to SQLite database")
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite: {e}")
            raise
    
    def _create_tables(self):
        """Create necessary tables in SQLite"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retry_count INTEGER DEFAULT 0,
                last_attempt TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE,
                message_data TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                webhook_response TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pending_created_at 
            ON pending_messages(created_at)
        ''')
        
        self.conn.commit()
    
    def store_pending_message(self, message_data: Dict) -> bool:
        """Store a message that needs to be sent"""
        try:
            if self.db_type == 'redis':
                return self._store_pending_redis(message_data)
            else:
                return self._store_pending_sqlite(message_data)
        except Exception as e:
            self.logger.error(f"Failed to store pending message: {e}")
            return False
    
    def _store_pending_redis(self, message_data: Dict) -> bool:
        """Store pending message in Redis"""
        message_id = f"pending:{int(time.time() * 1000)}"
        data = {
            'message_data': json.dumps(message_data),
            'created_at': time.time(),
            'retry_count': 0
        }
        self.redis_client.hset(message_id, mapping=data)
        self.redis_client.expire(message_id, 86400)  # 24 hours TTL
        return True
    
    def _store_pending_sqlite(self, message_data: Dict) -> bool:
        """Store pending message in SQLite"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO pending_messages (message_data) VALUES (?)',
            (json.dumps(message_data),)
        )
        self.conn.commit()
        return True
    
    def get_pending_messages(self, limit: int = None) -> List[Dict]:
        """Get pending messages to be sent"""
        try:
            if self.db_type == 'redis':
                return self._get_pending_redis(limit)
            else:
                return self._get_pending_sqlite(limit)
        except Exception as e:
            self.logger.error(f"Failed to get pending messages: {e}")
            return []
    
    def _get_pending_redis(self, limit: int = None) -> List[Dict]:
        """Get pending messages from Redis"""
        pattern = "pending:*"
        keys = self.redis_client.keys(pattern)
        
        if limit:
            keys = keys[:limit]
        
        messages = []
        for key in keys:
            data = self.redis_client.hgetall(key)
            if data:
                messages.append({
                    'id': key,
                    'message_data': json.loads(data['message_data']),
                    'created_at': float(data['created_at']),
                    'retry_count': int(data['retry_count'])
                })
        
        return sorted(messages, key=lambda x: x['created_at'])
    
    def _get_pending_sqlite(self, limit: int = None) -> List[Dict]:
        """Get pending messages from SQLite"""
        cursor = self.conn.cursor()
        query = 'SELECT * FROM pending_messages ORDER BY created_at ASC'
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            messages.append({
                'id': row['id'],
                'message_data': json.loads(row['message_data']),
                'created_at': row['created_at'],
                'retry_count': row['retry_count']
            })
        
        return messages
    
    def remove_pending_message(self, message_id) -> bool:
        """Remove a pending message after successful sending"""
        try:
            if self.db_type == 'redis':
                return self._remove_pending_redis(message_id)
            else:
                return self._remove_pending_sqlite(message_id)
        except Exception as e:
            self.logger.error(f"Failed to remove pending message: {e}")
            return False
    
    def _remove_pending_redis(self, message_id) -> bool:
        """Remove pending message from Redis"""
        return bool(self.redis_client.delete(message_id))
    
    def _remove_pending_sqlite(self, message_id) -> bool:
        """Remove pending message from SQLite"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM pending_messages WHERE id = ?', (message_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def update_retry_count(self, message_id, retry_count: int) -> bool:
        """Update retry count for a pending message"""
        try:
            if self.db_type == 'redis':
                return self._update_retry_redis(message_id, retry_count)
            else:
                return self._update_retry_sqlite(message_id, retry_count)
        except Exception as e:
            self.logger.error(f"Failed to update retry count: {e}")
            return False
    
    def _update_retry_redis(self, message_id, retry_count: int) -> bool:
        """Update retry count in Redis"""
        self.redis_client.hset(message_id, 'retry_count', retry_count)
        return True
    
    def _update_retry_sqlite(self, message_id, retry_count: int) -> bool:
        """Update retry count in SQLite"""
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE pending_messages SET retry_count = ?, last_attempt = CURRENT_TIMESTAMP WHERE id = ?',
            (retry_count, message_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def store_sent_message(self, message_id: str, message_data: Dict, webhook_response: str = None) -> bool:
        """Store a successfully sent message"""
        try:
            if self.db_type == 'redis':
                return self._store_sent_redis(message_id, message_data, webhook_response)
            else:
                return self._store_sent_sqlite(message_id, message_data, webhook_response)
        except Exception as e:
            self.logger.error(f"Failed to store sent message: {e}")
            return False
    
    def _store_sent_redis(self, message_id: str, message_data: Dict, webhook_response: str = None) -> bool:
        """Store sent message in Redis"""
        sent_id = f"sent:{message_id}"
        data = {
            'message_data': json.dumps(message_data),
            'sent_at': time.time(),
            'webhook_response': webhook_response or ''
        }
        self.redis_client.hset(sent_id, mapping=data)
        self.redis_client.expire(sent_id, 604800)  # 7 days TTL
        return True
    
    def _store_sent_sqlite(self, message_id: str, message_data: Dict, webhook_response: str = None) -> bool:
        """Store sent message in SQLite"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO sent_messages (message_id, message_data, webhook_response) VALUES (?, ?, ?)',
            (message_id, json.dumps(message_data), webhook_response)
        )
        self.conn.commit()
        return True
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            if self.db_type == 'redis':
                return self._get_stats_redis()
            else:
                return self._get_stats_sqlite()
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {}
    
    def _get_stats_redis(self) -> Dict:
        """Get statistics from Redis"""
        pending_keys = self.redis_client.keys("pending:*")
        sent_keys = self.redis_client.keys("sent:*")
        
        return {
            'pending_count': len(pending_keys),
            'sent_count': len(sent_keys),
            'database_type': 'redis'
        }
    
    def _get_stats_sqlite(self) -> Dict:
        """Get statistics from SQLite"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM pending_messages')
        pending_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sent_messages')
        sent_count = cursor.fetchone()[0]
        
        return {
            'pending_count': pending_count,
            'sent_count': sent_count,
            'database_type': 'sqlite'
        }
    
    def close(self):
        """Close database connections"""
        if self.db_type == 'redis' and hasattr(self, 'redis_client'):
            self.redis_client.close()
        elif hasattr(self, 'conn'):
            self.conn.close() 