"""
Thread Management Module
Manages multiple independent chat sessions.
"""
import uuid
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreadManager:
    """Manages multiple independent chat threads."""
    
    def __init__(
        self,
        db_path: str = "data/threads.db",
        max_history_turns: int = 6
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_history_turns = max_history_turns
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for threads with WAL mode for concurrency."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrent write performance
        cursor.execute('PRAGMA journal_mode=WAL')
        
        # Create threads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threads (
                thread_id TEXT PRIMARY KEY,
                session_key TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT,
                retrieval_debug_id TEXT,
                FOREIGN KEY (thread_id) REFERENCES threads (thread_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Thread database initialized at {self.db_path} with WAL mode")
    
    def create_thread(self, session_key: Optional[str] = None) -> str:
        """Create a new thread and return its ID."""
        thread_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO threads (thread_id, session_key, created_at, updated_at) VALUES (?, ?, ?, ?)',
            (thread_id, session_key, now, now)
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created thread {thread_id}")
        return thread_id
    
    def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        retrieval_debug_id: Optional[str] = None
    ):
        """Add a message to a thread."""
        now = datetime.utcnow().isoformat() + 'Z'
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            '''INSERT INTO messages (thread_id, role, content, timestamp, retrieval_debug_id)
               VALUES (?, ?, ?, ?, ?)''',
            (thread_id, role, content, now, retrieval_debug_id)
        )
        
        # Update thread's updated_at
        cursor.execute(
            'UPDATE threads SET updated_at = ? WHERE thread_id = ?',
            (now, thread_id)
        )
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Added message to thread {thread_id}: {role}")
    
    def get_thread_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get messages from a thread, optionally limited to recent N turns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if limit:
            cursor.execute(
                '''SELECT role, content, timestamp, retrieval_debug_id
                   FROM messages
                   WHERE thread_id = ?
                   ORDER BY id DESC
                   LIMIT ?''',
                (thread_id, limit * 2)  # Each turn has user + assistant message
            )
            rows = cursor.fetchall()[::-1]  # Reverse to get chronological order
        else:
            cursor.execute(
                '''SELECT role, content, timestamp, retrieval_debug_id
                   FROM messages
                   WHERE thread_id = ?
                   ORDER BY id ASC''',
                (thread_id,)
            )
            rows = cursor.fetchall()
        
        conn.close()
        
        messages = [
            {
                'role': row[0],
                'content': row[1],
                'timestamp': row[2],
                'retrieval_debug_id': row[3]
            }
            for row in rows
        ]
        
        return messages
    
    def get_recent_context(
        self,
        thread_id: str,
        max_turns: Optional[int] = None
    ) -> str:
        """Get recent conversation context for query expansion."""
        max_turns = max_turns or self.max_history_turns
        messages = self.get_thread_messages(thread_id, limit=max_turns)
        
        # Build context from user messages only (no assistant echo)
        user_messages = [
            msg['content'] for msg in messages if msg['role'] == 'user'
        ]
        
        return ' '.join(user_messages[-3:])  # Last 3 user messages
    
    def list_threads(self, limit: int = 50) -> List[Dict]:
        """List all threads."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT thread_id, session_key, created_at, updated_at
               FROM threads
               ORDER BY updated_at DESC
               LIMIT ?''',
            (limit,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        threads = [
            {
                'thread_id': row[0],
                'session_key': row[1],
                'created_at': row[2],
                'updated_at': row[3]
            }
            for row in rows
        ]
        
        return threads
    
    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread and all its messages."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete messages first
        cursor.execute('DELETE FROM messages WHERE thread_id = ?', (thread_id,))
        
        # Delete thread
        cursor.execute('DELETE FROM threads WHERE thread_id = ?', (thread_id,))
        
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        
        if deleted:
            logger.info(f"Deleted thread {thread_id}")
        
        return deleted
    
    def thread_exists(self, thread_id: str) -> bool:
        """Check if a thread exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM threads WHERE thread_id = ?', (thread_id,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists


def main():
    """CLI to test thread management."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage chat threads')
    parser.add_argument('command', choices=['new-thread', 'list-threads', 'say', 'history', 'delete'], help='Command')
    parser.add_argument('--thread-id', help='Thread ID')
    parser.add_argument('--message', help='Message content')
    parser.add_argument('--role', default='user', help='Message role')
    
    args = parser.parse_args()
    
    manager = ThreadManager()
    
    if args.command == 'new-thread':
        thread_id = manager.create_thread()
        print(f"Created thread: {thread_id}")
    
    elif args.command == 'list-threads':
        threads = manager.list_threads()
        print(f"\nThreads ({len(threads)}):")
        for thread in threads:
            print(f"  - {thread['thread_id']} (updated: {thread['updated_at']})")
    
    elif args.command == 'say':
        if not args.thread_id or not args.message:
            print("Error: --thread-id and --message required")
            return
        
        if not manager.thread_exists(args.thread_id):
            print(f"Error: Thread {args.thread_id} does not exist")
            return
        
        manager.add_message(args.thread_id, args.role, args.message)
        print(f"Added message to thread {args.thread_id}")
    
    elif args.command == 'history':
        if not args.thread_id:
            print("Error: --thread-id required")
            return
        
        messages = manager.get_thread_messages(args.thread_id)
        print(f"\nThread {args.thread_id} history:")
        for msg in messages:
            print(f"  [{msg['role']}] {msg['content']}")
    
    elif args.command == 'delete':
        if not args.thread_id:
            print("Error: --thread-id required")
            return
        
        if manager.delete_thread(args.thread_id):
            print(f"Deleted thread {args.thread_id}")
        else:
            print(f"Thread {args.thread_id} not found")


if __name__ == "__main__":
    main()
