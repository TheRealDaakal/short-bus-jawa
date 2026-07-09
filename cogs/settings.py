import logging

import discord
from discord import app_commands
from discord.ext import commands

from services import guild_settings_service
from services.permission_service import PermissionService

log = logging.getLogger(__name__)


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    settings = app_commands.Group(
        name="settings",
        description="Configure this server's bot settings",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    @settings.command(name="modlog", description="Set the channel moderation actions get logged to")
    @app_commands.describe(channel="The channel to post moderation logs in")
    async def modlog(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_mod_log_channel(interaction.guild_id, channel.id)

        await interaction.response.send_message(f"✅ Moderation log channel set to {channel.mention}.", ephemeral=True)

    @settings.command(name="raidchannel", description="Set the default channel raid announcements post in")
    @app_commands.describe(channel="The channel raid boards should be announced in")
    async def raidchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_raid_announce_channel(interaction.guild_id, channel.id)

        await interaction.response.send_message(f"✅ Raid announcement channel set to {channel.mention}.", ephemeral=True)

    @settings.command(name="newschannel", description="Set the channel SWTOR news & Cartel Market updates post in")
    @app_commands.describe(channel="The channel news updates should be posted in")
    async def newschannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_news_channel(interaction.guild_id, channel.id)

        await interaction.response.send_message(f"✅ News channel set to {channel.mention}.", ephemeral=True)

    @settings.command(name="ticketcategory", description="Set the category new support ticket channels get created under")
    @app_commands.describe(category="The category tickets should be created in")
    async def ticketcategory(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_ticket_category(interaction.guild_id, category.id)

        await interaction.response.send_message(f"✅ Ticket category set to **{category.name}**.", ephemeral=True)

    officerrole = app_commands.Group(
        name="officerrole",
        description="Manage which roles count as raid officers",
        parent=settings,
        default_permissions=discord.Permissions(manage_guild=True),
    )

    @officerrole.command(name="add", description="Add a role that counts as a raid officer")
    @app_commands.describe(role="Members with this role (or Administrator) can lock/finish raids and moderate")
    async def officerrole_add(self, interaction: discord.Interaction, role: discord.Role):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.add_officer_role(interaction.guild_id, role.id)

        await interaction.response.send_message(f"✅ {role.mention} added as a raid officer role.", ephemeral=True)

    @officerrole.command(name="remove", description="Remove a role from counting as a raid officer")
    @app_commands.describe(role="The role to stop treating as a raid officer")
    async def officerrole_remove(self, interaction: discord.Interaction, role: discord.Role):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        removed = guild_settings_service.remove_officer_role(interaction.guild_id, role.id)

        if removed:
            await interaction.response.send_message(f"✅ {role.mention} removed from raid officer roles.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{role.mention} wasn't configured as an officer role.", ephemeral=True)

    @settings.command(name="raidleaderrole", description="Set which role counts as a raid leader")
    @app_commands.describe(role="Members with this role can be highlighted as raid leaders")
    async def raidleaderrole(self, interaction: discord.Interaction, role: discord.Role):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_raid_leader_role(interaction.guild_id, role.id)

        await interaction.response.send_message(f"✅ Raid leader role set to {role.mention}.", ephemeral=True)

    @settings.command(name="welcomechannel", description="Set the channel new-member welcome messages post in")
    @app_commands.describe(channel="The channel welcome messages should be posted in")
    async def welcomechannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_welcome_channel(interaction.guild_id, channel.id)

        await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}.", ephemeral=True)

    @settings.command(name="welcomemessage", description="Set the new-member welcome message text")
    @app_commands.describe(
        message="Welcome message - supports {member}, {member_name}, {server}, {member_count} placeholders"
    )
    async def welcomemessage(self, interaction: discord.Interaction, message: str):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_welcome_message(interaction.guild_id, message)

        from cogs.welcome import format_welcome_message

        preview = format_welcome_message(message, interaction.user)

        await interaction.response.send_message(
            f"✅ Welcome message updated. Preview:\n{preview}",
            ephemeral=True,
        )

    @settings.command(name="leavemessage", description="Set the message posted to the welcome channel when a member leaves")
    @app_commands.describe(
        message="Leave message - supports {member}, {member_name}, {server}, {member_count} placeholders"
    )
    async def leavemessage(self, interaction: discord.Interaction, message: str):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_leave_message(interaction.guild_id, message)

        from cogs.welcome import format_welcome_message

        preview = format_welcome_message(message, interaction.user)

        await interaction.response.send_message(
            f"✅ Leave message updated. Preview:\n{preview}",
            ephemeral=True,
        )

    @settings.command(name="welcomedm", description="Set a DM sent to new members on join (leave blank/unset to not DM anyone)")
    @app_commands.describe(
        message="DM message - supports {member}, {member_name}, {server}, {member_count} placeholders"
    )
    async def welcomedm(self, interaction: discord.Interaction, message: str):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_welcome_dm_message(interaction.guild_id, message)

        from cogs.welcome import format_welcome_message

        preview = format_welcome_message(message, interaction.user)

        await interaction.response.send_message(
            f"✅ New members will now be DMed on join. Preview:\n{preview}",
            ephemeral=True,
        )

    @settings.command(name="joinrole", description="Set a role to auto-assign to every new member on join")
    @app_commands.describe(role="The role new members get automatically (e.g. a Quarantine/unverified role)")
    async def joinrole(self, interaction: discord.Interaction, role: discord.Role):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        bot_member = interaction.guild.me

        if role >= bot_member.top_role and not bot_member.guild_permissions.administrator:
            await interaction.response.send_message(
                f"⚠️ {role.mention} is above (or equal to) my highest role, so I won't be able to "
                f"assign it. Move my role above it in Server Settings > Roles first.",
                ephemeral=True,
            )
            return

        guild_settings_service.set_join_role(interaction.guild_id, role.id)

        await interaction.response.send_message(f"✅ New members will automatically get {role.mention}.", ephemeral=True)

    automod = app_commands.Group(
        name="automod",
        description="Configure automatic moderation (banned words, mention spam)",
        parent=settings,
        default_permissions=discord.Permissions(manage_guild=True),
    )

    @automod.command(name="enable", description="Turn on automod for this server")
    async def automod_enable(self, interaction: discord.Interaction):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_automod_enabled(interaction.guild_id, True)

        await interaction.response.send_message("✅ Automod is now **enabled**.", ephemeral=True)

    @automod.command(name="disable", description="Turn off automod for this server")
    async def automod_disable(self, interaction: discord.Interaction):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_automod_enabled(interaction.guild_id, False)

        await interaction.response.send_message("✅ Automod is now **disabled**.", ephemeral=True)

    @automod.command(name="addword", description="Add a word/phrase to the banned words filter")
    @app_commands.describe(word="The word or phrase to block (case-insensitive, matches anywhere in a message)")
    async def automod_addword(self, interaction: discord.Interaction, word: str):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.add_banned_word(interaction.guild_id, word)

        await interaction.response.send_message(f"✅ Added `{word}` to the banned words list.", ephemeral=True)

    @automod.command(name="removeword", description="Remove a word/phrase from the banned words filter")
    @app_commands.describe(word="The word or phrase to unblock")
    async def automod_removeword(self, interaction: discord.Interaction, word: str):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        removed = guild_settings_service.remove_banned_word(interaction.guild_id, word)

        if removed:
            await interaction.response.send_message(f"✅ Removed `{word}` from the banned words list.", ephemeral=True)
        else:
            await interaction.response.send_message(f"`{word}` wasn't in the banned words list.", ephemeral=True)

    @automod.command(name="listwords", description="List all banned words for this server")
    async def automod_listwords(self, interaction: discord.Interaction):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to view settings.", ephemeral=True)
            return

        words = guild_settings_service.get_banned_words(interaction.guild_id)

        if not words:
            await interaction.response.send_message("No banned words configured.", ephemeral=True)
            return

        await interaction.response.send_message(
            "**Banned words:**\n" + ", ".join(f"`{w}`" for w in words),
            ephemeral=True,
        )

    @automod.command(name="mentionlimit", description="Set the max mentions allowed in a single message")
    @app_commands.describe(limit="Messages with more mentions than this get removed (default 5)")
    async def automod_mentionlimit(self, interaction: discord.Interaction, limit: app_commands.Range[int, 1, 50]):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to change settings.", ephemeral=True)
            return

        guild_settings_service.set_automod_mention_limit(interaction.guild_id, limit)

        await interaction.response.send_message(f"✅ Mention limit set to {limit}.", ephemeral=True)

    @settings.command(name="view", description="View this server's current bot settings")
    async def view(self, interaction: discord.Interaction):
        if not PermissionService.can_manage_settings(interaction.user):
            await interaction.response.send_message("You don't have permission to view settings.", ephemeral=True)
            return

        mod_log_id = guild_settings_service.get_mod_log_channel(interaction.guild_id)
        raid_channel_id = guild_settings_service.get_raid_announce_channel(interaction.guild_id)
        officer_role_ids = guild_settings_service.get_officer_roles(interaction.guild_id)
        raid_leader_role_id = guild_settings_service.get_raid_leader_role(interaction.guild_id)
        welcome_channel_id = guild_settings_service.get_welcome_channel(interaction.guild_id)
        welcome_message = guild_settings_service.get_welcome_message(interaction.guild_id)
        leave_message = guild_settings_service.get_leave_message(interaction.guild_id)
        welcome_dm_message = guild_settings_service.get_welcome_dm_message(interaction.guild_id)
        join_role_id = guild_settings_service.get_join_role(interaction.guild_id)
        automod_enabled = guild_settings_service.get_automod_enabled(interaction.guild_id)
        automod_words = guild_settings_service.get_banned_words(interaction.guild_id)
        automod_mention_limit = guild_settings_service.get_automod_mention_limit(interaction.guild_id)
        news_channel_id = guild_settings_service.get_news_channel(interaction.guild_id)
        ticket_category_id = guild_settings_service.get_ticket_category(interaction.guild_id)

        embed = discord.Embed(title="⚙️ Server Settings", color=discord.Color.blue())
        embed.add_field(
            name="Mod Log Channel",
            value=f"<#{mod_log_id}>" if mod_log_id else "Not set",
            inline=False,
        )
        embed.add_field(
            name="Raid Announcement Channel",
            value=f"<#{raid_channel_id}>" if raid_channel_id else "Not set",
            inline=False,
        )
        embed.add_field(
            name="News Channel",
            value=f"<#{news_channel_id}>" if news_channel_id else "Not set (no SWTOR/Cartel Market news posted)",
            inline=False,
        )
        embed.add_field(
            name="Ticket Category",
            value=(
                f"<#{ticket_category_id}>" if ticket_category_id
                else "Not set (use /ticket panel after configuring this)"
            ),
            inline=False,
        )
        embed.add_field(
            name="Officer Roles",
            value=(
                "\n".join(f"<@&{role_id}>" for role_id in officer_role_ids)
                if officer_role_ids
                else "Not set (falls back to Administrator or a role named Officer/Raid Officer/Guild Master)"
            ),
            inline=False,
        )
        embed.add_field(
            name="Raid Leader Role",
            value=f"<@&{raid_leader_role_id}>" if raid_leader_role_id else "Not set",
            inline=False,
        )
        embed.add_field(
            name="Welcome Channel",
            value=f"<#{welcome_channel_id}>" if welcome_channel_id else "Not set (no welcome messages sent)",
            inline=False,
        )

        from cogs.welcome import DEFAULT_WELCOME_MESSAGE, DEFAULT_LEAVE_MESSAGE

        embed.add_field(
            name="Welcome Message",
            value=welcome_message or f"Default: {DEFAULT_WELCOME_MESSAGE}",
            inline=False,
        )
        embed.add_field(
            name="Leave Message",
            value=leave_message or f"Default: {DEFAULT_LEAVE_MESSAGE}",
            inline=False,
        )
        embed.add_field(
            name="Welcome DM",
            value=welcome_dm_message or "Not set (new members aren't DMed)",
            inline=False,
        )
        embed.add_field(
            name="Join Role",
            value=f"<@&{join_role_id}>" if join_role_id else "Not set (no role auto-assigned)",
            inline=False,
        )

        from cogs.automod import DEFAULT_MENTION_LIMIT

        embed.add_field(
            name="Automod",
            value=(
                f"{'✅ Enabled' if automod_enabled else '❌ Disabled'}\n"
                f"Banned words: {len(automod_words)}\n"
                f"Mention limit: {automod_mention_limit or DEFAULT_MENTION_LIMIT}"
            ),
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Settings(bot))
