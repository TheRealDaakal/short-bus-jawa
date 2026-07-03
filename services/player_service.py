from services.database import get_connection


def add_player(member):
    """Add a player to the database if they don't already exist."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO players
        (discord_id, discord_name)
        VALUES (?, ?)
    """, (
        member.id,
        str(member)
    ))

    conn.commit()
    conn.close()

    print(f"✅ Player added: {member}")
    