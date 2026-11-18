
import sqlite3
import secrets
import hashlib

from pathlib import Path
from datetime import datetime, timezone


DB_PATH = Path("data/users.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    return sqlite3.connect(DB_PATH)


def hash_api_key(api_key: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        api_key.encode("utf-8"),
        salt,
        200_000
    ).hex()


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                api_key_salt TEXT NOT NULL,
                api_key_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)


def create_user(username: str, role: str):
    allowed_roles = {
        "admin",
        "developer",
        "analyst",
        "guest"
    }

    if role not in allowed_roles:
        raise ValueError("Invalid role")

    api_key = secrets.token_urlsafe(32)
    salt = secrets.token_bytes(16)

    key_hash = hash_api_key(api_key, salt)

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (
                    username,
                    role,
                    api_key_salt,
                    api_key_hash,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    username,
                    role,
                    salt.hex(),
                    key_hash,
                    datetime.now(timezone.utc).isoformat()
                )
            )

    except sqlite3.IntegrityError:
        raise ValueError(f"Username '{username}' already exists")

    return api_key


def authenticate_api_key(api_key: str):
    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id, username, role, api_key_salt, api_key_hash
            FROM users
            WHERE is_active = 1
            """
        ).fetchall()

    for user_id, username, role, salt_hex, stored_hash in user:
        salt = bytes.fromhex(salt_hex)
        calculated_hash = hash_api_key(api_key, salt)

        if secrets.compare_digest(calculated_hash, stored_hash):
            return {
                "id": user_id,
                "username": username,
                "role": role
            }

    return None


def deactivate_user(username: str):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE users
            SET is_active = 0
            WHERE username = ?
            """,
            (username,)
        )

    return cursor.rowcount > 0

def activate_user(username: str):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE users
            SET is_active = 1
            WHERE username = ?
            """,
            (username,)
        )

    return cursor.rowcount > 0

def get_all_users():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, username, role, is_active, created_at
            FROM users
            ORDER BY id
            """
        ).fetchall()

    return [
        {
            "id": row[0],
            "username": row[1],
            "role": row[2],
            "is_active": bool(row[3]),
            "created_at": row[4]
        }
        for row in rows
    ]