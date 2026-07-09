import logging

from services.database import get_connection

log = logging.getLogger(__name__)


def log_action(
    guild_id: int,
    target_id: int,
    moderator_id: int,
    action: str,
    reason: str | None = None,
    duration_seconds: int | None = None,
) -> int:
    """Record a moderation action (kick/ban/unban/timeout/warn/clearwarnings)."""

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO mod_actions
                (guild_id, target_id, moderator_id, action, reason, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            guild_id,
            target_id,
            moderator_id,
            action,
            reason,
            duration_seconds,
        ))

        action_id = cursor.lastrowid

    log.info(
        "mod action logged: guild=%s target=%s mod=%s action=%s",
        guild_id, target_id, moderator_id, action,
    )

    return action_id


def get_warnings(guild_id: int, target_id: int) -> list[dict]:
    """Return all warnings for a user in a guild, newest first."""

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, moderator_id, reason, created_at
            FROM mod_actions
            WHERE guild_id = ? AND target_id = ? AND action = 'warn'
            ORDER BY created_at DESC
        """, (guild_id, target_id))

        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "moderator_id": row[1],
            "reason": row[2],
            "created_at": row[3],
        }
        for row in rows
    ]


def get_history(guild_id: int, target_id: int) -> list[dict]:
    """Return the full moderation history for a user in a guild."""

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, moderator_id, action, reason, duration_seconds, created_at
            FROM mod_actions
            WHERE guild_id = ? AND target_id = ?
            ORDER BY created_at DESC
        """, (guild_id, target_id))

        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "moderator_id": row[1],
            "action": row[2],
            "reason": row[3],
            "duration_seconds": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


def count_recent_actions(guild_id: int, target_id: int, action: str, window_seconds: int) -> int:
    """Count how many times this action was logged against a user in the last window_seconds."""

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM mod_actions
            WHERE guild_id = ? AND target_id = ? AND action = ?
              AND created_at >= datetime('now', ?)
        """, (guild_id, target_id, action, f"-{window_seconds} seconds"))

        row = cursor.fetchone()

    return row[0] if row else 0


def clear_warnings(guild_id: int, target_id: int) -> int:
    """Delete all warnings for a user in a guild. Returns count deleted."""

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM mod_actions
            WHERE guild_id = ? AND target_id = ? AND action = 'warn'
        """, (guild_id, target_id))

        deleted = cursor.rowcount

    log.info("cleared %s warnings for guild=%s target=%s", deleted, guild_id, target_id)

    return deleted
