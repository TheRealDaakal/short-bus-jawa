import json
import logging

import discord

from models.raid_member import RaidMember, StoredMember
from services import raid_storage
from services.raid_manager import RaidManager

log = logging.getLogger(__name__)


def _restore_members(guild: discord.Guild, entries: list[dict]) -> list[RaidMember]:
    members = []

    for entry in entries:
        user_id = entry["user_id"]
        member = guild.get_member(user_id) or StoredMember(
            id=user_id,
            display_name=entry.get("display_name") or "Unknown Member",
        )

        members.append(
            RaidMember(
                member=member,
                combat_style=entry.get("combat_style", ""),
                discipline=entry.get("discipline", ""),
            )
        )

    return members


async def restore_active_raids(bot) -> int:
    """
    Rebuilds RaidManager.active_raids from the database on startup, so
    raid boards posted before this process started keep working (and
    keep their signups) instead of every restart wiping them.

    Returns the number of raids restored.
    """

    restored = 0

    for row in raid_storage.get_active_raids():
        guild = bot.get_guild(row["guild_id"])
        if guild is None:
            continue

        channel = guild.get_channel(row["channel_id"])
        if channel is None:
            # Channel got deleted while the bot was down - nothing to
            # restore this raid to.
            continue

        try:
            message = await channel.fetch_message(row["message_id"])
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            # Board message got deleted (or we lost access) while the
            # bot was down - same as above, nothing left to restore.
            continue

        session = RaidManager.create_session(
            raid_id=row["id"],
            operation=row["operation"],
            difficulty=row["difficulty"],
            raid_date=row["raid_date"],
            raid_time=row["raid_time"],
            raid_leader=row["raid_leader"] or "",
            raid_leader_id=row["raid_leader_id"],
            faction=row["faction"] or "Empire",
            raid_size=row["raid_size"] or 8,
            raid_timestamp=row["raid_timestamp"],
            raid_end_timestamp=row["raid_end_timestamp"],
            raid_timezone=row["raid_timezone"] or "",
        )

        session.locked = bool(row["locked"])
        session.completed = bool(row["completed"])
        session.message = message
        session.message_id = message.id
        session.channel_id = channel.id

        roster = json.loads(row["roster_json"]) if row["roster_json"] else {}

        session.tanks = _restore_members(guild, roster.get("tanks", []))
        session.healers = _restore_members(guild, roster.get("healers", []))
        session.dps = _restore_members(guild, roster.get("dps", []))
        session.bench = _restore_members(guild, roster.get("bench", []))
        session.floaters = _restore_members(guild, roster.get("floaters", []))

        restored += 1

    if restored:
        log.info("Restored %d active raid(s) from the database", restored)

    return restored
