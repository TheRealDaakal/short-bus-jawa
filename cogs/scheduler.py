import logging
import random
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from services.raid_manager import RaidManager
from services import raid_template_service
from services.raid_poster import create_and_post_raid
from utils.constants import CLEANUP_MESSAGES, AUTO_DELETE_GRACE_MINUTES

log = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 60

_PING_CONTENT = {
    "everyone": "@everyone",
    "here": "@here",
}


class Scheduler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tick.start()

    def cog_unload(self):
        self.tick.cancel()

    @tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
    async def tick(self):
        now = int(time.time())

        # Snapshot the list since raids can be removed (auto-deleted)
        # partway through this loop.
        for raid_id, session in list(RaidManager.active_raids.items()):
            try:
                await self._process_raid(raid_id, session, now)
            except Exception:
                log.exception("Scheduler failed processing raid #%s", raid_id)

        for template in raid_template_service.get_active_templates():
            try:
                await self._process_template(template)
            except Exception:
                log.exception("Scheduler failed processing raid template #%s", template["id"])

    @tick.before_loop
    async def before_tick(self):
        await self.bot.wait_until_ready()

    async def _process_raid(self, raid_id: int, session, now: int):
        if session.completed:
            return

        if not session.raid_timestamp:
            return

        # If someone manually deleted the raid board message (e.g. the
        # raid got cancelled), stop tracking it entirely instead of still
        # firing reminders for a board that's no longer there.
        if not await self._board_still_exists(session):
            log.info("Raid #%s board was deleted - cancelling reminders", raid_id)
            RaidManager.remove_session(raid_id)
            return

        seconds_until_start = session.raid_timestamp - now

        # ---- 24 hour reminder ----
        if "24h" not in session.reminders_sent and seconds_until_start <= 24 * 3600:
            await self._send_reminder(session, "⏰ **24 hours** until raid time!")
            session.reminders_sent.add("24h")

        # ---- 30 minute reminder ----
        if "30m" not in session.reminders_sent and seconds_until_start <= 30 * 60:
            await self._send_reminder(session, "⏰ **30 minutes** until raid time!")
            session.reminders_sent.add("30m")

        # ---- Raid starting now: announce + auto-lock ----
        if "start" not in session.reminders_sent and seconds_until_start <= 0:
            await self._send_reminder(session, "🚀 **The raid is starting now!**")
            RaidManager.lock_raid(session)
            await RaidManager.refresh_board(session)
            session.reminders_sent.add("start")

        # ---- Auto-delete: 30 minutes after the raid ENDS ----
        # Falls back to 2h after start if this raid somehow has no end
        # time recorded (shouldn't happen for new raids, but keeps old
        # data from lingering forever).
        if session.raid_end_timestamp:
            delete_at = session.raid_end_timestamp + AUTO_DELETE_GRACE_MINUTES * 60
        else:
            delete_at = session.raid_timestamp + 2 * 3600

        if "deleted" not in session.reminders_sent and now >= delete_at:
            await self._auto_delete(raid_id, session)
            session.reminders_sent.add("deleted")

    async def _board_still_exists(self, session) -> bool:
        if not session.channel_id or not session.message_id:
            return True

        channel = self.bot.get_channel(session.channel_id)

        if channel is None:
            # Can't confirm either way (channel cache miss) - don't
            # assume deleted off a transient lookup failure.
            return True

        try:
            await channel.fetch_message(session.message_id)
            return True
        except discord.NotFound:
            return False
        except discord.HTTPException:
            return True

    async def _send_reminder(self, session, text: str):
        channel = self.bot.get_channel(session.channel_id)

        if channel is None:
            log.warning(
                "Reminder skipped for raid #%s - channel %s not found",
                session.raid_id, session.channel_id,
            )
            return

        try:
            await channel.send(text)
        except discord.HTTPException:
            log.exception("Failed to send reminder for raid #%s", session.raid_id)

    async def _auto_delete(self, raid_id: int, session):
        channel = self.bot.get_channel(session.channel_id)

        if channel is not None and session.message_id:
            try:
                message = session.message or await channel.fetch_message(session.message_id)
                await message.delete()
            except discord.NotFound:
                pass
            except discord.HTTPException:
                log.exception("Failed to delete raid board for raid #%s", raid_id)

            try:
                await channel.send(random.choice(CLEANUP_MESSAGES))
            except discord.HTTPException:
                pass

        log.info("Auto-deleted raid #%s", raid_id)
        RaidManager.remove_session(raid_id)

    # -------------------------
    # Recurring Raid Templates
    # -------------------------

    async def _process_template(self, template: dict):
        tz = ZoneInfo(template["timezone"])
        local_now = datetime.now(tz)

        time_of_day = datetime.strptime(template["time_of_day"], "%I:%M %p").time()

        # Find the next occurrence of this template's weekday/time that is
        # at or after right now (today if the time hasn't passed yet,
        # otherwise the matching day next week).
        days_ahead = (template["day_of_week"] - local_now.weekday()) % 7
        occurrence_date = local_now.date() + timedelta(days=days_ahead)
        occurrence_dt = datetime.combine(occurrence_date, time_of_day, tzinfo=tz)

        if occurrence_dt < local_now:
            occurrence_date += timedelta(days=7)
            occurrence_dt = datetime.combine(occurrence_date, time_of_day, tzinfo=tz)

        occurrence_key = occurrence_date.isoformat()

        if template["last_posted_date"] == occurrence_key:
            return

        post_at = occurrence_dt - timedelta(days=template["lead_days"])

        if local_now < post_at:
            return

        await self._fire_template(template, occurrence_dt, occurrence_key)

    async def _fire_template(self, template: dict, occurrence_dt: datetime, occurrence_key: str):
        guild = self.bot.get_guild(template["guild_id"])

        if guild is None:
            log.warning("Raid template #%s skipped - guild %s not found", template["id"], template["guild_id"])
            return

        channel = guild.get_channel(template["channel_id"])

        if channel is None:
            log.warning(
                "Raid template #%s skipped - channel %s not found",
                template["id"], template["channel_id"],
            )
            return

        creator = guild.get_member(template["created_by"]) or self.bot.user
        raid_timestamp = int(occurrence_dt.timestamp())

        try:
            await create_and_post_raid(
                guild_id=template["guild_id"],
                channel=channel,
                created_by=creator,
                operation=template["operation"],
                difficulty=template["difficulty"],
                raid_date=occurrence_dt.strftime("%m/%d/%Y"),
                raid_time=occurrence_dt.strftime("%I:%M %p").lstrip("0"),
                faction=template["faction"],
                raid_size=template["raid_size"],
                raid_timestamp=raid_timestamp,
                raid_end_timestamp=raid_timestamp + template["duration_minutes"] * 60,
                raid_timezone=template["timezone"],
                content=_PING_CONTENT.get(template["ping_type"]),
            )
        except discord.HTTPException:
            log.exception("Failed to auto-post raid from template #%s", template["id"])
            return

        raid_template_service.update_last_posted(template["id"], occurrence_key)

        log.info(
            "Raid template #%s (%s) fired for occurrence %s",
            template["id"], template["name"], occurrence_key,
        )


async def setup(bot):
    await bot.add_cog(Scheduler(bot))
