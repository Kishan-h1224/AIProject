
import json
import sqlite3

from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "approvals.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    return sqlite3.connect(
        str(DB_PATH),
        timeout=5
    )


def initialize_approval_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                conversation_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                arguments TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def create_approval(
    user_id: int,
    conversation_id: str,
    tool_name: str,
    arguments: dict
) -> str:

    approval_id = str(uuid4())

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO approvals (
                approval_id,
                user_id,
                conversation_id,
                tool_name,
                arguments,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            approval_id,
            user_id,
            conversation_id,
            tool_name,
            json.dumps(arguments),
            "pending",
            datetime.now(timezone.utc).isoformat()
        ))

    return approval_id


def get_pending_approval(
    approval_id: str,
    user_id: int
):
    with get_connection() as connection:
        connection.row_factory = sqlite3.Row

        row = connection.execute("""
            SELECT *
            FROM approvals
            WHERE approval_id = ?
              AND user_id = ?
              AND status = 'pending'
        """, (approval_id, user_id)).fetchone()

    if row is None:
        return None

    return {
        "approval_id": row["approval_id"],
        "user_id": row["user_id"],
        "conversation_id": row["conversation_id"],
        "tool_name": row["tool_name"],
        "arguments": json.loads(row["arguments"]),
        "status": row["status"],
        "created_at": row["created_at"]
    }


def claim_approval(
    approval_id: str,
    user_id: int
):
    """
    Atomically changes pending to approved.
    Only one request can claim the approval.
    """

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        cursor = connection.execute("""
            UPDATE approvals
            SET status = 'approved'
            WHERE approval_id = ?
              AND user_id = ?
              AND status = 'pending'
        """, (approval_id, user_id))

        if cursor.rowcount != 1:
            connection.rollback()
            return None

        row = connection.execute("""
            SELECT *
            FROM approvals
            WHERE approval_id = ?
        """, (approval_id,)).fetchone()

        connection.commit()

    return {
        "approval_id": row[0],
        "user_id": row[1],
        "conversation_id": row[2],
        "tool_name": row[3],
        "arguments": json.loads(row[4]),
        "status": row[5],
        "created_at": row[6]
    }


def reject_approval(
    approval_id: str,
    user_id: int
) -> bool:

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE approvals
            SET status = 'rejected'
            WHERE approval_id = ?
              AND user_id = ?
              AND status = 'pending'
        """, (approval_id, user_id))

    return cursor.rowcount == 1
