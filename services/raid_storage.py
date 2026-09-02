import json

from services.database import get_connection


def _serialize_members(members) -> list[dict]:
    return [
        {
            "user_id": member.id,
            "display_name": member.display_name,
            "combat_style": member.combat_style,
            "discipline": member.discipline,
        }
        for member in members
    ]


def save_raid_state(session):
    """
    Persists everything about a live raid that only ever lived in memory
    before - roster, lock/completed status, and where it's posted - so
    it survives a bot restart. Called after every signup, lock/unlock,
    finish, edit, or channel move.
    """

    roster_json = json.dumps({
        "tanks": _serialize_members(session.tanks),
        "healers": _serialize_members(session.healers),
        "dps": _serialize_members(session.dps),
        "bench": _serialize_members(session.bench),
        "floaters": _serialize_members(session.floaters),
    })

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE raids SET
                channel_id = ?,
                message_id = ?,
                faction = ?,
                raid_size = ?,
                raid_date = ?,
                raid_time = ?,
                raid_timestamp = ?,
                raid_end_timestamp = ?,
                raid_timezone = ?,
                raid_leader = ?,
                raid_leader_id = ?,
                locked = ?,
                completed = ?,
                roster_json = ?
            WHERE id = ?
        """, (
            session.channel_id,
            session.message_id,
            session.faction,
            session.raid_size,
            session.raid_date,
            session.raid_time,
            session.raid_timestamp,
            session.raid_end_timestamp,
            session.raid_timezone,
            session.raid_leader,
            session.raid_leader_id,
            int(session.locked),
            int(session.completed),
            roster_json,
            session.raid_id,
        ))


def mark_completed(raid_id: int):
    """
    Flags a raid as no longer active (finished or auto-deleted) so it's
    excluded from get_active_raids() and doesn't get resurrected on the
    next restart.
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("UPDATE raids SET completed = 1 WHERE id = ?", (raid_id,))


def get_active_raids() -> list[dict]:
    """
    All raids that were never finished/auto-deleted and actually made it
    to being posted (channel_id/message_id set) - used to rebuild
    RaidManager.active_raids on startup.
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM raids
            WHERE completed = 0
              AND channel_id IS NOT NULL
              AND message_id IS NOT NULL
        """)

        columns = [description[0] for description in cursor.description]

        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def create_raid(
    guild_id: int,
    operation: str,
    difficulty: str,
    raid_date: str,
    raid_time: str,
    created_by: int,
):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO raids (
                guild_id,
                operation,
                difficulty,
                raid_date,
                raid_time,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            guild_id,
            operation,
            difficulty,
            raid_date,
            raid_time,
            created_by,
        ))

        raid_id = cursor.lastrowid

    return raid_id


def get_raids_for_guild(guild_id: int) -> list[tuple]:
    """Return all raids ever scheduled for a specific guild."""

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM raids
            WHERE guild_id = ?
            ORDER BY created_at DESC
        """, (guild_id,))

        return cursor.fetchall()
