"""
Polls SWTOR-related RSS feeds and posts new items to each configured
server's news channel. There's no official Bioware API for this (Cartel
Market rotations in particular aren't published anywhere structured), so
this pulls from Swtorista, a well-established SWTOR fan community site
with real RSS feeds.
"""

import asyncio
import html
import logging
import random
import re

import discord
import feedparser
from discord.ext import commands, tasks

from services import guild_settings_service, news_service

log = logging.getLogger(__name__)

CHECK_INTERVAL_MINUTES = 15

NEWS_FEEDS = [
    {
        "name": "Cartel Market",
        "url": "https://swtorista.com/articles/category/swtor/news/cartel-market-sale/feed/",
        "emoji": "💰",
        "color": discord.Color.gold(),
        "flavor": [
            "🤖 Utinni! Look what's in the feed!",
            "🤖 Jawa found more shinies on the Cartel Bazaar!",
            "🤖 Utinni! Fresh junk just dropped on the Cartel Market!",
            "🤖 The scavenging droids found a sale...",
        ],
    },
    {
        "name": "SWTOR News",
        "url": "https://swtorista.com/articles/category/swtor/news/feed/",
        "emoji": "📰",
        "color": discord.Color.blue(),
        "flavor": [
            "🤖 Utinni! Word from the HoloNet...",
            "🤖 Jawa intercepted a transmission!",
            "🤖 Utinni! Fresh news from the galaxy!",
            "🤖 The scavenging droids bring word from the devs...",
        ],
    },
]

_TAG_RE = re.compile(r"<[^<]+?>")


def _entry_guid(entry) -> str:
    return entry.get("id") or entry.link


def _clean_summary(entry) -> str:
    summary = entry.get("summary", "")
    text = _TAG_RE.sub("", summary)
    text = html.unescape(text).strip()

    if len(text) > 300:
        text = text[:297] + "..."

    return text


def _entry_thumbnail(entry) -> str | None:
    media_thumbnail = entry.get("media_thumbnail")
    if media_thumbnail:
        return media_thumbnail[0].get("url")

    for link in entry.get("links", []):
        if link.get("type", "").startswith("image"):
            return link.get("href")

    return None


def build_news_embed(feed: dict, entry) -> discord.Embed:
    embed = discord.Embed(
        title=f"{feed['emoji']} {entry.title}",
        url=entry.link,
        description=_clean_summary(entry),
        color=feed["color"],
    )
    embed.set_footer(text=f"{feed['name']} • via Swtorista")

    thumbnail = _entry_thumbnail(entry)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    return embed


class News(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_feeds.start()

    def cog_unload(self):
        self.check_feeds.cancel()

    @tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
    async def check_feeds(self):
        for feed in NEWS_FEEDS:
            try:
                await self._check_feed(feed)
            except Exception:
                log.exception("Failed checking news feed %s", feed["name"])

    @check_feeds.before_loop
    async def before_check_feeds(self):
        await self.bot.wait_until_ready()

    async def _check_feed(self, feed: dict):
        parsed = await asyncio.to_thread(feedparser.parse, feed["url"])

        if not parsed.entries:
            log.warning("News feed %s returned no entries", feed["name"])
            return

        entries = list(reversed(parsed.entries))  # oldest first

        if not news_service.is_feed_initialized(feed["url"]):
            # First time seeing this feed - record everything currently in
            # it as "already posted" without actually posting, so turning
            # this on doesn't dump the feed's whole history into a channel.
            for entry in entries:
                news_service.mark_item_posted(_entry_guid(entry))
            news_service.mark_feed_initialized(feed["url"])
            log.info("Initialized news feed baseline for %s (%d items)", feed["name"], len(entries))
            return

        new_entries = [e for e in entries if not news_service.is_item_posted(_entry_guid(e))]

        if not new_entries:
            return

        channels = guild_settings_service.get_all_news_channels()

        for entry in new_entries:
            embed = build_news_embed(feed, entry)
            flavor_text = random.choice(feed["flavor"])

            for guild_id, channel_id in channels:
                guild = self.bot.get_guild(guild_id)
                if guild is None:
                    continue

                channel = guild.get_channel(channel_id)
                if channel is None:
                    continue

                try:
                    await channel.send(content=flavor_text, embed=embed)
                except discord.HTTPException:
                    log.exception(
                        "Failed to post news item to guild=%s channel=%s", guild_id, channel_id,
                    )

            news_service.mark_item_posted(_entry_guid(entry))


async def setup(bot):
    await bot.add_cog(News(bot))
