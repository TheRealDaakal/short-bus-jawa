import logging

from services.database import get_connection

log = logging.getLogger(__name__)

_COLUMNS = (
    "id", "guild_id", "name", "operation", "difficulty", "faction", "raid_size",
    "day_of_week", "time_of_day", "timezone", "duration_minutes", "lead_days",
    "channel_id", "ping_type", "created_by", "active", "last_posted_date",
)


def _row_to_dict(row) -> dict:
    return dict(zip(_COLUMNS, row))


def create_template(
    *,
    guild_id: int,
    name: str,
    operation: str,
    difficulty: str,
    faction: str,
    raid_size: int,
    day_of_week: int,
    time_of_day: str,
    timezone: str,
    duration_minutes: int,
    lead_days: int,
    channel_id: int,
    ping_type: str,
    created_by: int,
) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO raid_templates (
                guild_id, name, operation, difficulty, faction, raid_size,
                day_of_week, time_of_day, timezone, duration_minutes, lead_days,
                channel_id, ping_type, created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guild_id, name, operation, difficulty, faction, raid_size,
            day_of_week, time_of_day, timezone, duration_minutes, lead_days,
            channel_id, ping_type, created_by,
        ))

        template_id = cursor.lastrowid

    log.info("guild=%s raid_template created: #%s %r", guild_id, template_id, name)

    return template_id


def get_templates_for_guild(guild_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM raid_templates
            WHERE guild_id = ?
            ORDER BY id
        """, (guild_id,))

        rows = cursor.fetchall()

    return [_row_to_dict(row) for row in rows]


def get_active_templates() -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM raid_templates WHERE active = 1")

        rows = cursor.fetchall()

    return [_row_to_dict(row) for row in rows]


def get_template(template_id: int, guild_id: int) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM raid_templates
            WHERE id = ? AND guild_id = ?
        """, (template_id, guild_id))

        row = cursor.fetchone()

    return _row_to_dict(row) if row else None


def delete_template(template_id: int, guild_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM raid_templates
            WHERE id = ? AND guild_id = ?
        """, (template_id, guild_id))

        removed = cursor.rowcount > 0

    log.info("guild=%s raid_template deleted: #%s (removed=%s)", guild_id, template_id, removed)

    return removed


def set_active(template_id: int, guild_id: int, active: bool) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE raid_templates
            SET active = ?
            WHERE id = ? AND guild_id = ?
        """, (1 if active else 0, template_id, guild_id))

        updated = cursor.rowcount > 0

    return updated


def update_last_posted(template_id: int, occurrence_date: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE raid_templates
            SET last_posted_date = ?
            WHERE id = ?
        """, (occurrence_date, template_id))
