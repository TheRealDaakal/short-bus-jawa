import logging

import discord

from services.raid_manager import RaidManager
from services.raid_storage import create_raid
from utils.embed_builder import build_raid_embed

log = logging.getLogger(__name__)


async def create_and_post_raid(
    *,
    guild_id: int,
    channel: discord.abc.Messageable,
    created_by: discord.abc.User,
    operation: str,
    difficulty: str,
    raid_date: str,
    raid_time: str,
    faction: str = "Empire",
    raid_size: int = 8,
    raid_timestamp: int | None = None,
    raid_end_timestamp: int | None = None,
    raid_timezone: str = "",
    content: str | None = None,
):
    """
    Saves a raid to the database, creates its in-memory session, and posts
    the live signup board to a channel. Shared by the Raid Wizard and
    /raid spin so both paths stay in sync.

    Returns (raid_id, message).
    """

    from views.raid_view import RaidView
    from utils.banners import attach_banner

    raid_id = create_raid(
        guild_id=guild_id,
        operation=operation,
        difficulty=difficulty,
        raid_date=raid_date,
        raid_time=raid_time,
        created_by=created_by.id,
    )

    raid_session = RaidManager.create_session(
        raid_id=raid_id,
        operation=operation,
        difficulty=difficulty,
        raid_date=raid_date,
        raid_time=raid_time,
        raid_leader=created_by.display_name,
        raid_leader_id=created_by.id,
        faction=faction,
        raid_size=raid_size,
        raid_timestamp=raid_timestamp,
        raid_end_timestamp=raid_end_timestamp,
        raid_timezone=raid_timezone,
    )

    embed = build_raid_embed(raid_session)
    banner_file = attach_banner(embed, operation)

    send_kwargs = {
        "content": content,
        "embed": embed,
        "view": RaidView(raid_id),
    }
    if banner_file is not None:
        send_kwargs["file"] = banner_file

    message = await channel.send(**send_kwargs)

    raid_session.message = message
    raid_session.message_id = message.id
    raid_session.channel_id = channel.id

    log.info(
        "Raid #%s created in guild=%s channel=%s by %s",
        raid_id, guild_id, channel.id, created_by.id,
    )

    return raid_id, message
