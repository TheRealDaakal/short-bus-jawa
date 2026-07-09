import logging
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from services import moderation_service, guild_settings_service
from services.permission_service import PermissionService
from utils.duration import parse_duration, format_duration, InvalidDuration
from utils.mod_embed_builder import build_mod_log_embed

log = logging.getLogger(__name__)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    mod = app_commands.Group(
        name="mod",
        description="Moderation tools",
        default_permissions=discord.Permissions(moderate_members=True),
    )

    # -------------------------
    # Internal helpers
    # -------------------------

    @staticmethod
    def _guard_target(actor: discord.Member, target: discord.Member) -> str | None:
        """Returns an error string if the action shouldn't proceed, else None."""

        if target.id == actor.id:
            return "You can't moderate yourself."

        if target.bot and target.id == actor.guild.me.id:
            return "I can't moderate myself."

        if target.top_role >= actor.top_role and actor.id != actor.guild.owner_id:
            return "You can't moderate someone with an equal or higher role than you."

        if target.top_role >= actor.guild.me.top_role:
            return "My role is too low to moderate that user."

        return None

    async def _post_mod_log(self, guild: discord.Guild, embed: discord.Embed):
        channel_id = guild_settings_service.get_mod_log_channel(guild.id)

        if channel_id is None:
            return

        channel = guild.get_channel(channel_id)

        if channel is None:
            log.warning("Configured mod-log channel %s not found in guild %s", channel_id, guild.id)
            return

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            log.warning("Missing permission to post in mod-log channel for guild %s", guild.id)

    @staticmethod
    async def _dm_user(user: discord.abc.User, message: str):
        try:
            await user.send(message)
        except discord.Forbidden:
            # User has DMs closed - not a failure, just skip it.
            pass
        except discord.HTTPException:
            log.warning("Failed to DM user %s", user.id)

    # -------------------------
    # Kick
    # -------------------------

    @mod.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(user="The member to kick", reason="Why they're being kicked")
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = ""):
        actor = interaction.user

        if not PermissionService.can_kick(actor):
            await interaction.response.send_message("You don't have permission to kick members.", ephemeral=True)
            return

        error = self._guard_target(actor, user)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        await self._dm_user(user, f"You were kicked from **{interaction.guild.name}**.\nReason: {reason or 'No reason provided'}")

        try:
            await user.kick(reason=reason or f"Kicked by {actor}")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to kick that user.", ephemeral=True)
            return
        except discord.HTTPException as e:
            log.exception("Kick failed")
            await interaction.response.send_message(f"Kick failed: {e}", ephemeral=True)
            return

        moderation_service.log_action(interaction.guild_id, user.id, actor.id, "kick", reason)

        embed = build_mod_log_embed("kick", user, actor, reason)
        await self._post_mod_log(interaction.guild, embed)

        await interaction.response.send_message(f"👢 Kicked {user.mention}.", ephemeral=True)

    # -------------------------
    # Ban / Unban
    # -------------------------

    @mod.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(
        user="The member to ban",
        reason="Why they're being banned",
        delete_days="Days of their message history to delete (0-7)",
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "",
        delete_days: app_commands.Range[int, 0, 7] = 0,
    ):
        actor = interaction.user

        if not PermissionService.can_ban(actor):
            await interaction.response.send_message("You don't have permission to ban members.", ephemeral=True)
            return

        error = self._guard_target(actor, user)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        await self._dm_user(user, f"You were banned from **{interaction.guild.name}**.\nReason: {reason or 'No reason provided'}")

        try:
            await user.ban(reason=reason or f"Banned by {actor}", delete_message_days=delete_days)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban that user.", ephemeral=True)
            return
        except discord.HTTPException as e:
            log.exception("Ban failed")
            await interaction.response.send_message(f"Ban failed: {e}", ephemeral=True)
            return

        moderation_service.log_action(interaction.guild_id, user.id, actor.id, "ban", reason)

        embed = build_mod_log_embed("ban", user, actor, reason)
        await self._post_mod_log(interaction.guild, embed)

        await interaction.response.send_message(f"🔨 Banned {user.mention}.", ephemeral=True)

    @mod.command(name="unban", description="Unban a user by their ID")
    @app_commands.describe(user_id="The Discord ID of the user to unban", reason="Why they're being unbanned")
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = ""):
        actor = interaction.user

        if not PermissionService.can_ban(actor):
            await interaction.response.send_message("You don't have permission to unban members.", ephemeral=True)
            return

        try:
            target_id = int(user_id)
        except ValueError:
            await interaction.response.send_message("That doesn't look like a valid user ID.", ephemeral=True)
            return

        try:
            user = await self.bot.fetch_user(target_id)
            await interaction.guild.unban(user, reason=reason or f"Unbanned by {actor}")
        except discord.NotFound:
            await interaction.response.send_message("That user isn't banned, or the ID is invalid.", ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to unban users.", ephemeral=True)
            return
        except discord.HTTPException as e:
            log.exception("Unban failed")
            await interaction.response.send_message(f"Unban failed: {e}", ephemeral=True)
            return

        moderation_service.log_action(interaction.guild_id, target_id, actor.id, "unban", reason)

        embed = build_mod_log_embed("unban", user, actor, reason)
        await self._post_mod_log(interaction.guild, embed)

        await interaction.response.send_message(f"♻️ Unbanned {user.mention}.", ephemeral=True)

    # -------------------------
    # Timeout
    # -------------------------

    @mod.command(name="timeout", description="Temporarily timeout a member")
    @app_commands.describe(
        user="The member to timeout",
        duration="e.g. 10m, 1h, 3d (max 28d)",
        reason="Why they're being timed out",
    )
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str = ""):
        actor = interaction.user

        if not PermissionService.can_timeout(actor):
            await interaction.response.send_message("You don't have permission to timeout members.", ephemeral=True)
            return

        error = self._guard_target(actor, user)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        try:
            seconds = parse_duration(duration)
        except InvalidDuration as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        until = discord.utils.utcnow() + timedelta(seconds=seconds)

        try:
            await user.timeout(until, reason=reason or f"Timed out by {actor}")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to timeout that user.", ephemeral=True)
            return
        except discord.HTTPException as e:
            log.exception("Timeout failed")
            await interaction.response.send_message(f"Timeout failed: {e}", ephemeral=True)
            return

        duration_text = format_duration(seconds)

        moderation_service.log_action(interaction.guild_id, user.id, actor.id, "timeout", reason, seconds)

        embed = build_mod_log_embed("timeout", user, actor, reason, duration_text)
        await self._post_mod_log(interaction.guild, embed)

        await self._dm_user(user, f"You were timed out in **{interaction.guild.name}** for {duration_text}.\nReason: {reason or 'No reason provided'}")

        await interaction.response.send_message(f"⏱️ Timed out {user.mention} for {duration_text}.", ephemeral=True)

    @mod.command(name="untimeout", description="Remove an active timeout from a member")
    @app_commands.describe(user="The member to remove the timeout from")
    async def untimeout(self, interaction: discord.Interaction, user: discord.Member):
        actor = interaction.user

        if not PermissionService.can_timeout(actor):
            await interaction.response.send_message("You don't have permission to do that.", ephemeral=True)
            return

        try:
            await user.timeout(None, reason=f"Timeout removed by {actor}")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to update that user's timeout.", ephemeral=True)
            return
        except discord.HTTPException as e:
            log.exception("Untimeout failed")
            await interaction.response.send_message(f"Failed to remove timeout: {e}", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Removed timeout from {user.mention}.", ephemeral=True)

    # -------------------------
    # Warnings
    # -------------------------

    @mod.command(name="warn", description="Warn a member")
    @app_commands.describe(user="The member to warn", reason="Why they're being warned")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        actor = interaction.user

        if not PermissionService.can_warn(actor):
            await interaction.response.send_message("You don't have permission to warn members.", ephemeral=True)
            return

        error = self._guard_target(actor, user)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        moderation_service.log_action(interaction.guild_id, user.id, actor.id, "warn", reason)

        embed = build_mod_log_embed("warn", user, actor, reason)
        await self._post_mod_log(interaction.guild, embed)

        await self._dm_user(user, f"You were warned in **{interaction.guild.name}**.\nReason: {reason}")

        await interaction.response.send_message(f"⚠️ Warned {user.mention}.", ephemeral=True)

    @mod.command(name="warnings", description="View a member's warning history")
    @app_commands.describe(user="The member to check")
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        if not PermissionService.can_warn(interaction.user):
            await interaction.response.send_message("You don't have permission to view warnings.", ephemeral=True)
            return

        records = moderation_service.get_warnings(interaction.guild_id, user.id)

        if not records:
            await interaction.response.send_message(f"{user.mention} has no warnings.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"⚠️ Warnings for {user.display_name}",
            color=discord.Color.yellow(),
        )

        for record in records[:10]:
            embed.add_field(
                name=str(record["created_at"]),
                value=f"By <@{record['moderator_id']}>: {record['reason'] or 'No reason provided'}",
                inline=False,
            )

        if len(records) > 10:
            embed.set_footer(text=f"Showing 10 of {len(records)} warnings")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @mod.command(name="clearwarnings", description="Clear all warnings for a member")
    @app_commands.describe(user="The member whose warnings should be cleared")
    async def clearwarnings(self, interaction: discord.Interaction, user: discord.Member):
        actor = interaction.user

        if not PermissionService.can_ban(actor):
            # Clearing history is more sensitive than issuing a warning,
            # so it's gated behind the same permission as bans.
            await interaction.response.send_message("You don't have permission to clear warnings.", ephemeral=True)
            return

        count = moderation_service.clear_warnings(interaction.guild_id, user.id)

        moderation_service.log_action(interaction.guild_id, user.id, actor.id, "clearwarnings", f"Cleared {count} warning(s)")

        embed = build_mod_log_embed("clearwarnings", user, actor, f"Cleared {count} warning(s)")
        await self._post_mod_log(interaction.guild, embed)

        await interaction.response.send_message(f"🧹 Cleared {count} warning(s) for {user.mention}.", ephemeral=True)

    # -------------------------
    # Message Cleanup
    # -------------------------

    @mod.command(name="purge", description="Bulk delete recent messages in this channel")
    @app_commands.describe(
        count="How many recent messages to delete (1-100)",
        user="Only delete messages from this member (optional)",
    )
    async def purge(
        self,
        interaction: discord.Interaction,
        count: app_commands.Range[int, 1, 100],
        user: discord.Member = None,
    ):
        actor = interaction.user

        if not PermissionService.can_manage_messages(actor):
            await interaction.response.send_message("You don't have permission to delete messages.", ephemeral=True)
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("This can only be used in a text channel.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        def check(message: discord.Message) -> bool:
            return user is None or message.author.id == user.id

        try:
            deleted = await interaction.channel.purge(
                limit=count,
                check=check,
                reason=f"Purged by {actor}",
            )
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to delete messages in this channel.", ephemeral=True)
            return
        except discord.HTTPException as e:
            log.exception("Purge failed")
            await interaction.followup.send(f"Purge failed: {e}", ephemeral=True)
            return

        reason = f"Purged {len(deleted)} message(s) in #{interaction.channel.name}"
        if user:
            reason += f" from {user}"

        moderation_service.log_action(interaction.guild_id, actor.id, actor.id, "purge", reason)

        embed = build_mod_log_embed("purge", actor, actor, reason)
        await self._post_mod_log(interaction.guild, embed)

        await interaction.followup.send(f"🧹 Deleted {len(deleted)} message(s).", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
