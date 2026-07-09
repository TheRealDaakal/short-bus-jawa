import logging

from services.database import get_connection

log = logging.getLogger(__name__)


def set_user_timezone(user_id: int, tz_name: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_settings (user_id, timezone)
            VALUES (?, ?)
            ON CONFLICT (user_id) DO UPDATE SET timezone = excluded.timezone
        """, (user_id, tz_name))

    log.info("user=%s timezone set to %s", user_id, tz_name)


def get_user_timezone(user_id: int) -> str | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timezone
            FROM user_settings
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()

    return row[0] if row else None
