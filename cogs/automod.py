import logging
from datetime import timedelta

import discord
from discord.ext import commands

from services import guild_settings_service, moderation_service
from utils.mod_embed_builder import build_mod_log_embed

log = logging.getLogger(__name__)

DEFAULT_MENTION_LIMIT = 5

# Escalate to a timeout if a member racks up this many automod violations
# within this window.
ESCALATION_VIOLATION_COUNT = 3
ESCALATION_WINDOW_SECONDS = 10 * 60
ESCALATION_TIMEOUT_SECONDS = 10 * 60


class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        if not guild_settings_service.get_automod_enabled(message.guild.id):
            return

        # Officers/mods are exempt from automod.
        if message.author.guild_permissions.manage_messages:
            return

        reason = self._check_banned_words(message) or self._check_mention_spam(message)

        if reason is None:
            return

        await self._handle_violation(message, reason)

    def _check_banned_words(self, message: discord.Message) -> str | None:
        banned_words = guild_settings_service.get_banned_words(message.guild.id)

        if not banned_words:
            return None

        content_lower = message.content.lower()

        for word in banned_words:
            if word in content_lower:
                return f"Used a banned word ({word})"

        return None

    def _check_mention_spam(self, message: discord.Message) -> str | None:
        limit = guild_settings_service.get_automod_mention_limit(message.guild.id) or DEFAULT_MENTION_LIMIT

        mention_count = len(message.mentions) + len(message.role_mentions)

        if mention_count > limit:
            return f"Mentioned {mention_count} users/roles at once (limit {limit})"

        return None

    async def _handle_violation(self, message: discord.Message, reason: str):
        try:
            await message.delete()
        except discord.HTTPException:
            pass

        try:
            await message.author.send(
                f"Your message in **{message.guild.name}** was removed by automod.\nReason: {reason}"
            )
        except discord.HTTPException:
            pass

        moderation_service.log_action(
            message.guild.id, message.author.id, self.bot.user.id, "automod", reason,
        )

        embed = build_mod_log_embed("automod", message.author, self.bot.user, reason)
        await self._post_mod_log(message.guild, embed)

        recent_violations = moderation_service.count_recent_actions(
            message.guild.id, message.author.id, "automod", ESCALATION_WINDOW_SECONDS,
        )

        if recent_violations >= ESCALATION_VIOLATION_COUNT:
            await self._escalate(message)

    async def _escalate(self, message: discord.Message):
        member = message.author
        until = discord.utils.utcnow() + timedelta(seconds=ESCALATION_TIMEOUT_SECONDS)

        try:
            await member.timeout(until, reason="Automod: repeated violations")
        except discord.HTTPException:
            log.warning("Failed to auto-timeout %s in guild %s", member.id, message.guild.id)
            return

        reason = (
            f"Timed out for {ESCALATION_TIMEOUT_SECONDS // 60} minutes after "
            f"{ESCALATION_VIOLATION_COUNT} automod violations in "
            f"{ESCALATION_WINDOW_SECONDS // 60} minutes"
        )

        moderation_service.log_action(
            message.guild.id, member.id, self.bot.user.id,
            "automod_timeout", reason, ESCALATION_TIMEOUT_SECONDS,
        )

        embed = build_mod_log_embed("automod_timeout", member, self.bot.user, reason)
        await self._post_mod_log(message.guild, embed)

    async def _post_mod_log(self, guild: discord.Guild, embed: discord.Embed):
        channel_id = guild_settings_service.get_mod_log_channel(guild.id)

        if channel_id is None:
            return

        channel = guild.get_channel(channel_id)

        if channel is None:
            return

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(AutoMod(bot))
