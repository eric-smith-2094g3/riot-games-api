import sqlite3
import json
from pathlib import Path

DB_PATH = Path.home() / ".lol_cache.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Setup tables for account metadata and full match payloads."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                game_name TEXT NOT NULL,
                tag_line TEXT NOT NULL,
                puuid TEXT PRIMARY KEY,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,
                game_creation INTEGER DEFAULT 0,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def get_cached_account(game_name: str, tag_line: str):
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT puuid FROM accounts WHERE lower(game_name) = lower(?) AND lower(tag_line) = lower(?)",
            (game_name, tag_line),
        )
        row = cur.fetchone()
        return row["puuid"] if row else None


def save_account(game_name: str, tag_line: str, puuid: str):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO accounts (game_name, tag_line, puuid, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(puuid) DO UPDATE SET
                game_name=excluded.game_name,
                tag_line=excluded.tag_line,
                updated_at=CURRENT_TIMESTAMP
            """,
            (game_name, tag_line, puuid),
        )


def get_cached_match(match_id: str):
    with get_connection() as conn:
        cur = conn.execute("SELECT data FROM matches WHERE match_id = ?", (match_id,))
        row = cur.fetchone()
        if row:
            return json.loads(row["data"])
        return None


def save_match(match_id: str, data: dict):
    raw = json.dumps(data)
    game_creation = data.get("info", {}).get("gameCreation", 0)
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO matches (match_id, game_creation, data) VALUES (?, ?, ?)",
            (match_id, game_creation, raw),
        )
