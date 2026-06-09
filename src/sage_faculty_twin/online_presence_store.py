from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .config import AppSettings


@dataclass(slots=True)
class OnlinePresenceSnapshot:
    window_seconds: int
    online_visitors: int
    online_authenticated_users: int
    active_conversations: int


class OnlinePresenceStore:
    def __init__(self, settings: AppSettings) -> None:
        self._path = settings.online_presence_dir
        self._path.mkdir(parents=True, exist_ok=True)
        self._db_path = self._path / "online_presence.sqlite3"
        self._retention_seconds = max(3600, int(settings.online_presence_retention_seconds))
        self._default_window_seconds = max(60, int(settings.online_presence_window_seconds))
        self._ensure_database()

    def record_heartbeat(
        self,
        *,
        client_id: str,
        conversation_id: str | None,
        student_email: str | None,
        is_authenticated: bool,
        window_seconds: int | None = None,
    ) -> OnlinePresenceSnapshot:
        now = datetime.now(UTC)
        sanitized_client_id = client_id.strip()
        sanitized_conversation_id = (conversation_id or "").strip() or None
        sanitized_email = (student_email or "").strip().lower() or None
        resolved_window_seconds = max(60, int(window_seconds or self._default_window_seconds))

        self._ensure_database()
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                INSERT INTO online_presence (
                    client_id,
                    conversation_id,
                    student_email,
                    is_authenticated,
                    last_seen_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(client_id) DO UPDATE SET
                    conversation_id = excluded.conversation_id,
                    student_email = excluded.student_email,
                    is_authenticated = excluded.is_authenticated,
                    last_seen_at = excluded.last_seen_at
                """,
                (
                    sanitized_client_id,
                    sanitized_conversation_id,
                    sanitized_email,
                    1 if is_authenticated else 0,
                    now.isoformat(),
                ),
            )
            self._prune_expired_rows(connection, now=now)
            connection.commit()

        return self.snapshot(window_seconds=resolved_window_seconds, now=now)

    def snapshot(
        self,
        *,
        window_seconds: int | None = None,
        now: datetime | None = None,
    ) -> OnlinePresenceSnapshot:
        resolved_window_seconds = max(60, int(window_seconds or self._default_window_seconds))
        current_time = now or datetime.now(UTC)
        cutoff = (current_time - timedelta(seconds=resolved_window_seconds)).isoformat()

        self._ensure_database()
        with sqlite3.connect(self._db_path) as connection:
            online_visitors = int(
                connection.execute(
                    "SELECT COUNT(DISTINCT client_id) FROM online_presence WHERE last_seen_at >= ?",
                    (cutoff,),
                ).fetchone()[0]
                or 0
            )
            online_authenticated_users = int(
                connection.execute(
                    """
                    SELECT COUNT(DISTINCT student_email)
                    FROM online_presence
                    WHERE last_seen_at >= ?
                      AND is_authenticated = 1
                      AND student_email IS NOT NULL
                      AND student_email != ''
                    """,
                    (cutoff,),
                ).fetchone()[0]
                or 0
            )
            active_conversations = int(
                connection.execute(
                    """
                    SELECT COUNT(DISTINCT conversation_id)
                    FROM online_presence
                    WHERE last_seen_at >= ?
                      AND conversation_id IS NOT NULL
                      AND conversation_id != ''
                    """,
                    (cutoff,),
                ).fetchone()[0]
                or 0
            )

        return OnlinePresenceSnapshot(
            window_seconds=resolved_window_seconds,
            online_visitors=online_visitors,
            online_authenticated_users=online_authenticated_users,
            active_conversations=active_conversations,
        )

    def _ensure_database(self) -> None:
        self._path.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS online_presence (
                    client_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    student_email TEXT,
                    is_authenticated INTEGER NOT NULL,
                    last_seen_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_online_presence_last_seen_at
                ON online_presence(last_seen_at)
                """
            )
            connection.commit()

    def _prune_expired_rows(self, connection: sqlite3.Connection, *, now: datetime) -> None:
        cutoff = (now - timedelta(seconds=self._retention_seconds)).isoformat()
        connection.execute(
            "DELETE FROM online_presence WHERE last_seen_at < ?",
            (cutoff,),
        )
