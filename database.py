import os
import sqlite3
from datetime import datetime

DB_DIR = os.path.join(os.path.expanduser("~"), ".video-downloader")
DB_PATH = os.path.join(DB_DIR, "data.db")

_CREATE_CONFIG = """
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""

_CREATE_HISTORY = """
CREATE TABLE IF NOT EXISTS download_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    title TEXT DEFAULT '',
    thumbnail TEXT DEFAULT '',
    uploader TEXT DEFAULT '',
    duration TEXT DEFAULT '',
    video_format TEXT DEFAULT '',
    audio_format TEXT DEFAULT '',
    file_path TEXT DEFAULT '',
    file_size INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    error_msg TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    completed_at TEXT DEFAULT ''
)
"""


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        if self.db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_CREATE_CONFIG)
        self._conn.execute(_CREATE_HISTORY)
        self._conn.commit()

    def get_config(self, key, default=None):
        row = self._conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_config(self, key, value):
        self._conn.execute(
            "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
            (key, value, value),
        )
        self._conn.commit()

    def add_history(self, record: dict) -> int:
        now = datetime.now().isoformat()
        cursor = self._conn.execute(
            """INSERT INTO download_history
               (url, title, thumbnail, uploader, duration, video_format, audio_format,
                file_path, file_size, status, error_msg, created_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.get("url", ""),
                record.get("title", ""),
                record.get("thumbnail", ""),
                record.get("uploader", ""),
                record.get("duration", ""),
                record.get("video_format", ""),
                record.get("audio_format", ""),
                record.get("file_path", ""),
                record.get("file_size", 0),
                record.get("status", "pending"),
                record.get("error_msg", ""),
                record.get("created_at", now),
                record.get("completed_at", ""),
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    def update_history(self, history_id: int, **kwargs):
        if not kwargs:
            return
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [history_id]
        self._conn.execute(f"UPDATE download_history SET {sets} WHERE id = ?", values)
        self._conn.commit()

    def get_history(self, page=1, size=20):
        offset = (page - 1) * size
        total = self._conn.execute("SELECT COUNT(*) FROM download_history").fetchone()[0]
        rows = self._conn.execute(
            "SELECT * FROM download_history ORDER BY id DESC LIMIT ? OFFSET ?", (size, offset)
        ).fetchall()
        items = [dict(r) for r in rows]
        return {"total": total, "page": page, "size": size, "items": items}

    def get_history_item(self, history_id: int):
        row = self._conn.execute("SELECT * FROM download_history WHERE id = ?", (history_id,)).fetchone()
        return dict(row) if row else None

    def delete_history(self, history_id: int) -> bool:
        cursor = self._conn.execute("DELETE FROM download_history WHERE id = ?", (history_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def clear_history(self) -> int:
        cursor = self._conn.execute("DELETE FROM download_history")
        self._conn.commit()
        return cursor.rowcount
