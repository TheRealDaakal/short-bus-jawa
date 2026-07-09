from services.database import get_connection


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
