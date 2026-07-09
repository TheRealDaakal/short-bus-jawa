import logging

from services.database import get_connection

log = logging.getLogger(__name__)


def _ensure_row(cursor, guild_id: int):
    cursor.execute("""
        INSERT OR IGNORE INTO guild_settings (guild_id)
        VALUES (?)
    """, (guild_id,))


def set_mod_log_channel(guild_id: int, channel_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_row(cursor, guild_id)

        cursor.execute("""
            UPDATE guild_settings
            SET mod_log_channel_id = ?
            WHERE guild_id = ?
        """, (channel_id, guild_id))

    log.info("guild=%s mod_log_channel set to %s", guild_id, channel_id)


def get_mod_log_channel(guild_id: int) -> int | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT mod_log_channel_id
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))

        row = cursor.fetchone()

    return row[0] if row else None


def set_raid_announce_channel(guild_id: int, channel_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_row(cursor, guild_id)

        cursor.execute("""
            UPDATE guild_settings
            SET raid_announce_channel_id = ?
            WHERE guild_id = ?
        """, (channel_id, guild_id))

    log.info("guild=%s raid_announce_channel set to %s", guild_id, channel_id)


def get_raid_announce_channel(guild_id: int) -> int | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT raid_announce_channel_id
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))

        row = cursor.fetchone()

    return row[0] if row else None


def add_officer_role(guild_id: int, role_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO officer_roles (guild_id, role_id)
            VALUES (?, ?)
        """, (guild_id, role_id))

    log.info("guild=%s officer_role added: %s", guild_id, role_id)


def remove_officer_role(guild_id: int, role_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM officer_roles
            WHERE guild_id = ? AND role_id = ?
        """, (guild_id, role_id))

        removed = cursor.rowcount > 0

    log.info("guild=%s officer_role removed: %s", guild_id, role_id)

    return removed


def get_officer_roles(guild_id: int) -> list[int]:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT role_id
            FROM officer_roles
            WHERE guild_id = ?
        """, (guild_id,))

        rows = cursor.fetchall()

    return [row[0] for row in rows]


def set_raid_leader_role(guild_id: int, role_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_row(cursor, guild_id)

        cursor.execute("""
            UPDATE guild_settings
            SET raid_leader_role_id = ?
            WHERE guild_id = ?
        """, (role_id, guild_id))

    log.info("guild=%s raid_leader_role set to %s", guild_id, role_id)


def get_raid_leader_role(guild_id: int) -> int | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT raid_leader_role_id
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))

        row = cursor.fetchone()

    return row[0] if row else None


def set_welcome_channel(guild_id: int, channel_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_row(cursor, guild_id)

        cursor.execute("""
            UPDATE guild_settings
            SET welcome_channel_id = ?
            WHERE guild_id = ?
        """, (channel_id, guild_id))

    log.info("guild=%s welcome_channel set to %s", guild_id, channel_id)


def get_welcome_channel(guild_id: int) -> int | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT welcome_channel_id
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))

        row = cursor.fetchone()

    return row[0] if row else None


def set_welcome_message(guild_id: int, message: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_row(cursor, guild_id)

        cursor.execute("""
            UPDATE guild_settings
            SET welcome_message = ?
            WHERE guild_id = ?
        """, (message, guild_id))

    log.info("guild=%s welcome_message updated", guild_id)


def get_welcome_message(guild_id: int) -> str | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT welcome_message
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))

        row = cursor.fetchone()

    return row[0] if row else None


def set_join_role(guild_id: int, role_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_row(cursor, guild_id)

        cursor.execute("""
            UPDATE guild_settings
            SET join_role_id = ?
            WHERE guild_id = ?
        """, (role_id, guild_id))

    log.info("guild=%s join_role set to %s", guild_id, role_id)


def get_join_role(guild_id: int) -> int | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT join_role_id
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))

        row = cursor.fetchone()

    return row[0] if row else None


def set_automod_enabled(guild_id: int, enabled: bool) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_row(cursor, guild_id)

        cursor.execute("""
            UPDATE guild_settings
            SET automod_enabled = ?
            WHERE guild_id = ?
        """, (1 if enabled else 0, guild_id))

    log.info("guild=%s automod_enabled set to %s", guild_id, enabled)


def get_automod_enabled(guild_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT automod_enabled
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))

        row = cursor.fetchone()

    return bool(row[0]) if row else False


def set_automod_mention_limit(guild_id: int, limit: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_row(cursor, guild_id)

        cursor.execute("""
            UPDATE guild_settings
            SET automod_mention_limit = ?
            WHERE guild_id = ?
        """, (limit, guild_id))

    log.info("guild=%s automod_mention_limit set to %s", guild_id, limit)


def get_automod_mention_limit(guild_id: int) -> int | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT automod_mention_limit
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))

        row = cursor.fetchone()

    return row[0] if row else None


def add_banned_word(guild_id: int, word: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO automod_banned_words (guild_id, word)
            VALUES (?, ?)
        """, (guild_id, word.lower()))

    log.info("guild=%s banned_word added", guild_id)


def remove_banned_word(guild_id: int, word: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM automod_banned_words
            WHERE guild_id = ? AND word = ?
        """, (guild_id, word.lower()))

        removed = cursor.rowcount > 0

    log.info("guild=%s banned_word removed: %s", guild_id, removed)

    return removed


def set_news_channel(guild_id: int, channel_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_row(cursor, guild_id)

        cursor.execute("""
            UPDATE guild_settings
            SET news_channel_id = ?
            WHERE guild_id = ?
        """, (channel_id, guild_id))

    log.info("guild=%s news_channel set to %s", guild_id, channel_id)


def get_news_channel(guild_id: int) -> int | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT news_channel_id
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))

        row = cursor.fetchone()

    return row[0] if row else None


def get_all_news_channels() -> list[tuple[int, int]]:
    """Returns (guild_id, channel_id) for every guild with a news channel configured."""

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT guild_id, news_channel_id
            FROM guild_settings
            WHERE news_channel_id IS NOT NULL
        """)

        rows = cursor.fetchall()

    return [(row[0], row[1]) for row in rows]


def get_banned_words(guild_id: int) -> list[str]:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT word
            FROM automod_banned_words
            WHERE guild_id = ?
        """, (guild_id,))

        rows = cursor.fetchall()

    return [row[0] for row in rows]


def set_ticket_category(guild_id: int, category_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_row(cursor, guild_id)

        cursor.execute("""
            UPDATE guild_settings
            SET ticket_category_id = ?
            WHERE guild_id = ?
        """, (category_id, guild_id))

    log.info("guild=%s ticket_category set to %s", guild_id, category_id)


def get_ticket_category(guild_id: int) -> int | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ticket_category_id
            FROM guild_settings
            WHERE guild_id = ?
        """, (guild_id,))

        row = cursor.fetchone()

    return row[0] if row else None
