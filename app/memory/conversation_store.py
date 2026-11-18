
import sqlite3

from pathlib import Path
from datetime import datetime, timezone


DB_PATH = Path("data/conversations.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_conversation_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def save_message(user_id, conversation_id, role, message):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversations (
                user_id,
                conversation_id,
                role,
                message,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                conversation_id,
                role,
                message,
                datetime.now(timezone.utc).isoformat()
            )
        )


def get_conversation(user_id, conversation_id):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, message, created_at
            FROM conversations
            WHERE user_id = ? AND conversation_id = ?
            ORDER BY id
            """,
            (user_id, conversation_id)
        ).fetchall()

    return [
        {
            "role": row[0],
            "message": row[1],
            "created_at": row[2]
        }
        for row in rows
    ]
