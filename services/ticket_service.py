import logging

from services.database import get_connection

log = logging.getLogger(__name__)

_COLUMNS = (
    "id", "guild_id", "channel_id", "opened_by",
    "status", "closed_by", "opened_at", "closed_at",
)


def _row_to_dict(row) -> dict:
    return dict(zip(_COLUMNS, row))


def create_ticket(guild_id: int, channel_id: int, opened_by: int) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tickets (guild_id, channel_id, opened_by)
            VALUES (?, ?, ?)
        """, (guild_id, channel_id, opened_by))

        ticket_id = cursor.lastrowid

    log.info("guild=%s ticket #%s opened by %s in channel=%s", guild_id, ticket_id, opened_by, channel_id)

    return ticket_id


def get_open_ticket_for_user(guild_id: int, user_id: int) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM tickets
            WHERE guild_id = ? AND opened_by = ? AND status = 'open'
        """, (guild_id, user_id))

        row = cursor.fetchone()

    return _row_to_dict(row) if row else None


def get_ticket_by_channel(channel_id: int) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM tickets WHERE channel_id = ?
        """, (channel_id,))

        row = cursor.fetchone()

    return _row_to_dict(row) if row else None


def close_ticket(ticket_id: int, closed_by: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tickets
            SET status = 'closed', closed_by = ?, closed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (closed_by, ticket_id))

    log.info("ticket #%s closed by %s", ticket_id, closed_by)
