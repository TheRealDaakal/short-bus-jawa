import logging

from services.database import get_connection

log = logging.getLogger(__name__)


def is_feed_initialized(feed_url: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1 FROM news_feed_state WHERE feed_url = ?
        """, (feed_url,))

        return cursor.fetchone() is not None


def mark_feed_initialized(feed_url: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO news_feed_state (feed_url)
            VALUES (?)
        """, (feed_url,))

    log.info("news feed initialized: %s", feed_url)


def is_item_posted(guid: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1 FROM news_posted_items WHERE guid = ?
        """, (guid,))

        return cursor.fetchone() is not None


def mark_item_posted(guid: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO news_posted_items (guid)
            VALUES (?)
        """, (guid,))
