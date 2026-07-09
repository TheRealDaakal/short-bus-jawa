import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path

log = logging.getLogger(__name__)

# Database location
DATABASE_FILE = Path("database") / "short_bus_jawa.db"


@contextmanager
def get_connection():
    """
    Context-managed connection to the SQLite database.

    Ensures the connection is always closed, commits on success,
    and rolls back automatically if an exception happens inside
    the `with` block - so a bad query can't silently leave the
    database in a half-written state or leak connections.
    """

    DATABASE_FILE.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DATABASE_FILE)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        log.exception("Database error - transaction rolled back")
        raise
    finally:
        conn.close()


def initialize_database():
    """Create all required database tables (idempotent)."""

    log.info("Initializing database at %s", DATABASE_FILE)

    with get_connection() as conn:
        cursor = conn.cursor()

        # Raids table - guild-scoped so multiple servers don't share
        # each other's raid history.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                guild_id INTEGER NOT NULL,

                operation TEXT NOT NULL,
                difficulty TEXT NOT NULL,

                raid_date TEXT NOT NULL,
                raid_time TEXT NOT NULL,

                created_by INTEGER NOT NULL,

                tanks_needed INTEGER DEFAULT 2,
                healers_needed INTEGER DEFAULT 2,
                dps_needed INTEGER DEFAULT 4,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_raids_guild
            ON raids (guild_id)
        """)

        # Per-guild configuration (mod-log channel, etc).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                mod_log_channel_id INTEGER,
                raid_announce_channel_id INTEGER,
                officer_role_id INTEGER,
                raid_leader_role_id INTEGER
            )
        """)

        # Defensive migration: if a guild_settings table already exists
        # from an earlier version without these columns, add them now.
        # SQLite has no "ADD COLUMN IF NOT EXISTS", so we just ignore the
        # error if the column is already there.
        for column in ("officer_role_id", "raid_leader_role_id"):
            try:
                cursor.execute(f"ALTER TABLE guild_settings ADD COLUMN {column} INTEGER")
            except sqlite3.OperationalError:
                pass

        try:
            cursor.execute("ALTER TABLE guild_settings ADD COLUMN welcome_channel_id INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE guild_settings ADD COLUMN welcome_message TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE guild_settings ADD COLUMN join_role_id INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE guild_settings ADD COLUMN automod_enabled INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE guild_settings ADD COLUMN automod_mention_limit INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE guild_settings ADD COLUMN news_channel_id INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE guild_settings ADD COLUMN ticket_category_id INTEGER")
        except sqlite3.OperationalError:
            pass

        # Support tickets - each open ticket is its own private channel;
        # this table is the persistent record of who opened what and
        # when, since the channel itself gets deleted on close.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                opened_by INTEGER NOT NULL,

                status TEXT NOT NULL DEFAULT 'open',
                closed_by INTEGER,

                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tickets_guild
            ON tickets (guild_id)
        """)

        # Banned words are many-per-guild, same pattern as officer_roles.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automod_banned_words (
                guild_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                PRIMARY KEY (guild_id, word)
            )
        """)

        # Officer roles are many-per-guild (a server may want e.g. both
        # "Raid Officer" and "Guild Master" to count), so they live in
        # their own table rather than a single column on guild_settings.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS officer_roles (
                guild_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, role_id)
            )
        """)

        # One-time migration: carry over any single officer role already
        # set on guild_settings (from before multi-role support existed)
        # into the new table.
        cursor.execute("""
            INSERT OR IGNORE INTO officer_roles (guild_id, role_id)
            SELECT guild_id, officer_role_id FROM guild_settings
            WHERE officer_role_id IS NOT NULL
        """)

        # Personal preferences, keyed by user rather than guild - a
        # member's timezone doesn't change depending on which server
        # they're in.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                timezone TEXT
            )
        """)

        # Recurring raid templates - the scheduler checks these each tick
        # and auto-posts a real raid board `lead_days` before each
        # occurrence, so e.g. "every Tuesday 8pm" reposts itself without
        # anyone having to run /raid schedule manually each week.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raid_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,

                operation TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                faction TEXT NOT NULL,
                raid_size INTEGER NOT NULL,

                day_of_week INTEGER NOT NULL,
                time_of_day TEXT NOT NULL,
                timezone TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                lead_days INTEGER NOT NULL DEFAULT 3,

                channel_id INTEGER NOT NULL,
                ping_type TEXT NOT NULL DEFAULT 'everyone',

                created_by INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                last_posted_date TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_raid_templates_guild
            ON raid_templates (guild_id)
        """)

        # SWTOR news feed tracking - which feeds have had their initial
        # baseline established (so enabling the feature doesn't dump a
        # feed's entire history into a channel at once), and which
        # individual items have already been posted (so restarts or
        # multiple feeds covering the same item don't duplicate posts).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_feed_state (
                feed_url TEXT PRIMARY KEY,
                initialized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_posted_items (
                guid TEXT PRIMARY KEY,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Moderation action audit log: kicks, bans, timeouts, warns, etc.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mod_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                guild_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,

                action TEXT NOT NULL,
                reason TEXT,

                -- populated only for timeouts
                duration_seconds INTEGER,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mod_actions_guild_target
            ON mod_actions (guild_id, target_id)
        """)

    log.info("Database initialized")
