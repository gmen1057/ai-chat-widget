"""SQLite storage implementation."""

import sqlite3
import json
from typing import List
from datetime import datetime
from .base import Storage, Message


class SQLiteStorage(Storage):
    """SQLite-based storage."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                page_context TEXT,
                INDEX idx_session (session_id)
            )
        """)

        conn.commit()
        conn.close()

    async def save_message(self, message: Message) -> None:
        """Save a message."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO messages (session_id, role, content, timestamp, page_context)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                message.session_id,
                message.role,
                message.content,
                message.timestamp.isoformat(),
                json.dumps(message.page_context),
            ),
        )

        conn.commit()
        conn.close()

    async def get_messages(self, session_id: str, limit: int = 50) -> List[Message]:
        """Get messages for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT session_id, role, content, timestamp, page_context
            FROM messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
        """,
            (session_id, limit),
        )

        rows = cursor.fetchall()
        conn.close()

        # Convert to Message objects
        messages = []
        for row in reversed(rows):  # Reverse to get chronological order
            messages.append(
                Message(
                    session_id=row[0],
                    role=row[1],
                    content=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    page_context=json.loads(row[4]) if row[4] else {},
                )
            )

        return messages

    async def delete_session(self, session_id: str) -> None:
        """Delete all messages for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))

        conn.commit()
        conn.close()

    async def get_all_sessions(self) -> List[str]:
        """Get all session IDs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT session_id FROM messages")

        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]
