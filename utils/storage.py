"""
Зберігання побачених подій у SQLite для дедублікації.
"""

import hashlib
import json
import logging
import sqlite3
from pathlib import Path

log = logging.getLogger("storage")


class Storage:
    def __init__(self, db_path: str = "events.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_events (
                    event_id  TEXT PRIMARY KEY,
                    title     TEXT,
                    date      TEXT,
                    city      TEXT,
                    source    TEXT,
                    url       TEXT,
                    seen_at   DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        log.info(f"Storage ініціалізовано: {self.db_path}")

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def make_id(self, event: dict) -> str:
        """Генерує унікальний ID події по ключових полях."""
        key = "|".join([
            (event.get("title") or "").strip().lower(),
            (event.get("date")  or "").strip(),
            (event.get("city")  or "").strip().lower(),
        ])
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def exists(self, event_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_events WHERE event_id = ?", (event_id,)
            ).fetchone()
            return row is not None

    def save(self, event_id: str, event: dict):
        with self._conn() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO seen_events
                   (event_id, title, date, city, source, url)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    event_id,
                    event.get("title", ""),
                    event.get("date", ""),
                    event.get("city", ""),
                    event.get("source", ""),
                    event.get("url", ""),
                ),
            )

    def count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM seen_events").fetchone()[0]

    def recent(self, limit: int = 10) -> list[dict]:
        """Останні N збережених подій (для дебагу)."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT title, date, city, source, seen_at FROM seen_events "
                "ORDER BY seen_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"title": r[0], "date": r[1], "city": r[2], "source": r[3], "seen_at": r[4]}
            for r in rows
        ]
