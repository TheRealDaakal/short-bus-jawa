import logging
import random
import asyncio
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands

from views.wizard_view import WizardView
from utils.wizard_embed_builder import build_wizard_embed
from services.wizard_service import WizardService
from services.raid_poster import create_and_post_raid
from services import user_settings_service, raid_template_service
from services.permission_service import PermissionService
from utils.swtor_content import (
    all_operations, all_lair_bosses, available_difficulties, available_raid_sizes, DIFFICULTIES,
)
from utils.constants import DEFAULT_RAID_DURATION_MINUTES, RAID_DURATIONS
from utils.timezones import COMMON_TIMEZONES
from utils.banners import attach_banner

log = logging.getLogger(__name__)

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class Raid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    raid = app_commands.Group(
        name="raid",
        description="Raid management"
    )

    @raid.command(
        name="spin",
        description="Spin the SWTOR Operations Wheel and instantly create an 8-man raid"
    )
    async def spin(self, interaction: discord.Interaction):

        operations = all_operations()
        winner = random.choice(operations)
        difficulty = random.choice(available_difficulties(winner))

        embed = discord.Embed(
            title="🎡 Short Bus Jawa Operations Wheel",
            description="🚌 Jawa kicks the wheel...",
            color=discord.Color.orange(),
        )
        await interaction.response.send_message(embed=embed)

        try:
            from utils.wheel_animation import build_spin_gif

            # Rendering is CPU-bound (Pillow) - run off the event loop so
            # it doesn't stall the bot while frames are drawn.
            gif_buffer = await asyncio.to_thread(build_spin_gif, winner)
            gif_file = discord.File(gif_buffer, filename="wheel_spin.gif")

            spin_embed = discord.Embed(
                title="🎡 Short Bus Jawa Operations Wheel",
                description="🎡 Spinning...",
                color=discord.Color.orange(),
            )
            spin_embed.set_image(url="attachment://wheel_spin.gif")

            await interaction.edit_original_response(embed=spin_embed, attachments=[gif_file])

            await asyncio.sleep(2.2)
        except Exception:
            # If the wheel animation fails for any reason (render error,
            # rate limit, etc.), don't let it block the actual reveal and
            # raid creation below.
            log.exception("Wheel spin animation failed - continuing to reveal")

        reveal_embed = discord.Embed(
            title="🎉 THE WHEEL HAS SPOKEN!",
            description=(
                f"🏆 **{winner}**\n\n"
                f"⚔️ {difficulty}\n\n"
                f"🚌 Time to build your raid!"
            ),
            color=discord.Color.gold(),
        )
        banner_file = attach_banner(reveal_embed, winner)

        try:
            if banner_file is not None:
                await interaction.edit_original_response(embed=reveal_embed, attachments=[banner_file])
            else:
                await interaction.edit_original_response(embed=reveal_embed)
        except discord.HTTPException:
            log.exception("Failed to show wheel reveal frame")

        try:
            now_utc = datetime.now(dt_timezone.utc)
            now_ts = int(now_utc.timestamp())

            tz_name = user_settings_service.get_user_timezone(interaction.user.id)
            display_time = now_utc.astimezone(ZoneInfo(tz_name)) if tz_name else now_utc

            raid_id, message = await create_and_post_raid(
                guild_id=interaction.guild_id,
                channel=interaction.channel,
                created_by=interaction.user,
                operation=winner,
                difficulty=difficulty,
                raid_date=display_time.strftime("%m/%d/%Y"),
                raid_time=display_time.strftime("%I:%M %p"),
                raid_size=8,
                raid_timestamp=now_ts,
                raid_end_timestamp=now_ts + DEFAULT_RAID_DURATION_MINUTES * 60,
                raid_timezone=tz_name or "UTC",
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to post the raid board here.",
                ephemeral=True,
            )
            return
        except Exception:
            log.exception("Failed to create raid from /raid spin")
            await interaction.followup.send(
                "❌ Something went wrong creating the raid. Please try again.",
                ephemeral=True,
            )
            return

    @raid.command(
        name="schedule",
        description="Create a new raid"
    )
    async def schedule(self, interaction: discord.Interaction):

        WizardService.create_session(interaction.user.id)

        session = WizardService.get_session(interaction.user.id)

        await interaction.response.send_message(
            embed=build_wizard_embed(session),
            view=WizardView(interaction.user.id),
            ephemeral=True,
        )

    @raid.command(
        name="timezone",
        description="Set your personal timezone (used to show /raid spin's creation time)"
    )
    @app_commands.describe(timezone="Your timezone")
    @app_commands.choices(timezone=[
        app_commands.Choice(name=label, value=tz_name)
        for label, tz_name in COMMON_TIMEZONES
    ])
    async def timezone_cmd(self, interaction: discord.Interaction, timezone: app_commands.Choice[str]):

        user_settings_service.set_user_timezone(interaction.user.id, timezone.value)

        await interaction.response.send_message(
            f"✅ Your timezone is set to **{timezone.name}**.",
            ephemeral=True,
        )

    # -------------------------
    # Recurring Raid Templates
    # -------------------------

    template = app_commands.Group(
        name="template",
        description="Manage recurring raid templates",
        parent=raid,
    )

    @template.command(name="create", description="Create a recurring raid template (auto-posts each week)")
    @app_commands.describe(
        name="A label for this template (e.g. 'Tuesday Ops Night')",
        operation="Operation or Lair Boss",
        difficulty="Raid difficulty",
        faction="Empire or Republic",
        raid_size="8 or 16 player raid",
        day="Day of the week this raid repeats on",
        time="Raid start time, e.g. 7:30 PM",
        timezone="Timezone the time above is in",
        channel="Channel to announce the raid in",
        duration="How long the raid runs before auto-deleting (default 2 hours)",
        ping="Who gets pinged when it's posted (default @everyone)",
        lead_days="How many days before the raid to post the signup board (default 3)",
    )
    @app_commands.choices(
        operation=[
            app_commands.Choice(name=n, value=n)
            for n in (all_operations() + all_lair_bosses())
        ],
        difficulty=[app_commands.Choice(name=d, value=d) for d in DIFFICULTIES],
        faction=[
            app_commands.Choice(name="Empire", value="Empire"),
            app_commands.Choice(name="Republic", value="Republic"),
        ],
        raid_size=[
            app_commands.Choice(name="8-Player", value=8),
            app_commands.Choice(name="16-Player", value=16),
        ],
        day=[app_commands.Choice(name=d, value=i) for i, d in enumerate(_WEEKDAYS)],
        timezone=[app_commands.Choice(name=label, value=tz) for label, tz in COMMON_TIMEZONES],
        duration=[app_commands.Choice(name=label, value=minutes) for label, minutes in RAID_DURATIONS],
        ping=[
            app_commands.Choice(name="@everyone", value="everyone"),
            app_commands.Choice(name="@here", value="here"),
            app_commands.Choice(name="No Ping", value="none"),
        ],
    )
    async def template_create(
        self,
        interaction: discord.Interaction,
        name: str,
        operation: app_commands.Choice[str],
        difficulty: app_commands.Choice[str],
        faction: app_commands.Choice[str],
        raid_size: app_commands.Choice[int],
        day: app_commands.Choice[int],
        time: str,
        timezone: app_commands.Choice[str],
        channel: discord.TextChannel,
        duration: app_commands.Choice[int] = None,
        ping: app_commands.Choice[str] = None,
        lead_days: app_commands.Range[int, 0, 14] = 3,
    ):
        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message(
                "❌ Only raid officers can create recurring raid templates.",
                ephemeral=True,
            )
            return

        if difficulty.value not in available_difficulties(operation.value):
            await interaction.response.send_message(
                f"⚠️ {operation.value} doesn't have {difficulty.value}.",
                ephemeral=True,
            )
            return

        if raid_size.value not in available_raid_sizes(operation.value):
            await interaction.response.send_message(
                f"⚠️ {operation.value} doesn't support {raid_size.value}-player raids.",
                ephemeral=True,
            )
            return

        raw_time = time.strip().upper().replace(".", "")

        parsed_time = None
        for fmt in ("%I:%M %p", "%I %p", "%H:%M"):
            try:
                parsed_time = datetime.strptime(raw_time, fmt)
                break
            except ValueError:
                continue

        if parsed_time is None:
            await interaction.response.send_message(
                "⚠️ That doesn't look like a valid time. Try formats like 7:30 PM or 19:30.",
                ephemeral=True,
            )
            return

        duration_minutes = duration.value if duration else DEFAULT_RAID_DURATION_MINUTES
        ping_type = ping.value if ping else "everyone"
        time_label = parsed_time.strftime("%I:%M %p").lstrip("0")

        template_id = raid_template_service.create_template(
            guild_id=interaction.guild_id,
            name=name,
            operation=operation.value,
            difficulty=difficulty.value,
            faction=faction.value,
            raid_size=raid_size.value,
            day_of_week=day.value,
            time_of_day=time_label,
            timezone=timezone.value,
            duration_minutes=duration_minutes,
            lead_days=lead_days,
            channel_id=channel.id,
            ping_type=ping_type,
            created_by=interaction.user.id,
        )

        await interaction.response.send_message(
            f"✅ Template **{name}** created (#{template_id}): every **{_WEEKDAYS[day.value]}** at "
            f"**{time_label} {timezone.name}**, posted **{lead_days} day(s)** ahead in {channel.mention}.",
            ephemeral=True,
        )

    @template.command(name="list", description="List this server's recurring raid templates")
    async def template_list(self, interaction: discord.Interaction):
        templates = raid_template_service.get_templates_for_guild(interaction.guild_id)

        if not templates:
            await interaction.response.send_message("No raid templates configured yet.", ephemeral=True)
            return

        embed = discord.Embed(title="🔁 Recurring Raid Templates", color=discord.Color.blue())

        for t in templates:
            status = "✅ Active" if t["active"] else "⏸️ Paused"
            embed.add_field(
                name=f"#{t['id']} - {t['name']}",
                value=(
                    f"{status}\n"
                    f"{t['operation']} ({t['difficulty']}, {t['raid_size']}-Player)\n"
                    f"Every **{_WEEKDAYS[t['day_of_week']]}** at {t['time_of_day']} ({t['timezone']})\n"
                    f"Posts {t['lead_days']} day(s) ahead in <#{t['channel_id']}>"
                ),
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @template.command(name="delete", description="Delete a recurring raid template")
    @app_commands.describe(template_id="The template's ID (see /raid template list)")
    async def template_delete(self, interaction: discord.Interaction, template_id: int):
        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message("❌ Only raid officers can delete templates.", ephemeral=True)
            return

        removed = raid_template_service.delete_template(template_id, interaction.guild_id)

        if removed:
            await interaction.response.send_message(f"✅ Template #{template_id} deleted.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No template #{template_id} found.", ephemeral=True)

    @template.command(name="pause", description="Pause a recurring raid template")
    @app_commands.describe(template_id="The template's ID (see /raid template list)")
    async def template_pause(self, interaction: discord.Interaction, template_id: int):
        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message("❌ Only raid officers can pause templates.", ephemeral=True)
            return

        updated = raid_template_service.set_active(template_id, interaction.guild_id, False)

        if updated:
            await interaction.response.send_message(f"⏸️ Template #{template_id} paused.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No template #{template_id} found.", ephemeral=True)

    @template.command(name="resume", description="Resume a paused raid template")
    @app_commands.describe(template_id="The template's ID (see /raid template list)")
    async def template_resume(self, interaction: discord.Interaction, template_id: int):
        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message("❌ Only raid officers can resume templates.", ephemeral=True)
            return

        updated = raid_template_service.set_active(template_id, interaction.guild_id, True)

        if updated:
            await interaction.response.send_message(f"✅ Template #{template_id} resumed.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No template #{template_id} found.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Raid(bot))