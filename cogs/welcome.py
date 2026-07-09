import logging

import discord
from discord.ext import commands

from services import guild_settings_service

log = logging.getLogger(__name__)

DEFAULT_WELCOME_MESSAGE = "👋 Welcome {member} to {server}! Glad to have you aboard."
DEFAULT_LEAVE_MESSAGE = "👋 {member_name} has left {server}."


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def format_welcome_message(template: str, member: discord.Member) -> str:
    return template.format_map(_SafeDict(
        member=member.mention,
        member_name=member.display_name,
        server=member.guild.name,
        member_count=member.guild.member_count,
    ))


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self._assign_join_role(member)
        await self._send_welcome_message(member)
        await self._send_welcome_dm(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self._send_leave_message(member)

    async def _assign_join_role(self, member: discord.Member):
        role_id = guild_settings_service.get_join_role(member.guild.id)

        if role_id is None:
            return

        role = member.guild.get_role(role_id)

        if role is None:
            log.warning(
                "Join role skipped for guild=%s - role %s not found",
                member.guild.id, role_id,
            )
            return

        try:
            await member.add_roles(role, reason="Auto-assigned on join")
        except discord.Forbidden:
            log.warning(
                "Missing permission to assign join role for guild=%s - check "
                "the bot's role is above %s and it has Manage Roles",
                member.guild.id, role.name,
            )
        except discord.HTTPException:
            log.exception("Failed to assign join role for guild=%s", member.guild.id)

    async def _send_welcome_message(self, member: discord.Member):
        channel_id = guild_settings_service.get_welcome_channel(member.guild.id)

        if channel_id is None:
            return

        channel = member.guild.get_channel(channel_id)

        if channel is None:
            log.warning(
                "Welcome message skipped for guild=%s - channel %s not found",
                member.guild.id, channel_id,
            )
            return

        template = guild_settings_service.get_welcome_message(member.guild.id) or DEFAULT_WELCOME_MESSAGE

        try:
            await channel.send(format_welcome_message(template, member))
        except discord.HTTPException:
            log.exception("Failed to send welcome message for guild=%s", member.guild.id)

    async def _send_welcome_dm(self, member: discord.Member):
        template = guild_settings_service.get_welcome_dm_message(member.guild.id)

        if not template:
            # DMing new members is opt-in - no template configured means
            # don't send one, rather than DMing a generic default nobody asked for.
            return

        try:
            await member.send(format_welcome_message(template, member))
        except discord.Forbidden:
            # Member has DMs closed - not a failure, just skip it.
            pass
        except discord.HTTPException:
            log.exception("Failed to DM welcome message to %s in guild=%s", member.id, member.guild.id)

    async def _send_leave_message(self, member: discord.Member):
        channel_id = guild_settings_service.get_welcome_channel(member.guild.id)

        if channel_id is None:
            return

        channel = member.guild.get_channel(channel_id)

        if channel is None:
            log.warning(
                "Leave message skipped for guild=%s - channel %s not found",
                member.guild.id, channel_id,
            )
            return

        template = guild_settings_service.get_leave_message(member.guild.id) or DEFAULT_LEAVE_MESSAGE

        try:
            await channel.send(format_welcome_message(template, member))
        except discord.HTTPException:
            log.exception("Failed to send leave message for guild=%s", member.guild.id)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
