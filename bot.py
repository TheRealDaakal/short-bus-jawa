import asyncio
import logging
import sys

import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.logging_config import setup_logging
from services.database import initialize_database

setup_logging(level=getattr(logging, config.LOG_LEVEL, logging.INFO))
log = logging.getLogger(__name__)

intents = discord.Intents.default()

# Privileged intent - required to receive on_member_join for welcome
# messages. Must also be turned on for this bot in the Discord Developer
# Portal under Bot > Privileged Gateway Intents > Server Members Intent,
# or login will fail.
intents.members = True

# Privileged intent - required for automod's banned-word filter to see
# message.content. Must also be turned on for this bot in the Discord
# Developer Portal under Bot > Privileged Gateway Intents > Message
# Content Intent, or login will fail. Mention-spam detection in automod
# works fine without this - only the word filter needs it.
intents.message_content = True

EXTENSIONS = [
    "cogs.raid",
    "cogs.moderation",
    "cogs.settings",
    "cogs.scheduler",
    "cogs.welcome",
    "cogs.automod",
    "cogs.news",
    "cogs.tickets",
]


class RaidBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):
        for extension in EXTENSIONS:
            try:
                await self.load_extension(extension)
                log.info("Loaded extension: %s", extension)
            except Exception:
                # A single broken cog shouldn't take the whole bot down -
                # log it loudly and keep going with everything else.
                log.exception("Failed to load extension: %s", extension)

        # Persistent views (timeout=None) must be re-registered on every
        # startup, or their buttons stop responding on messages sent
        # before this process started.
        from views.ticket_views import TicketPanelView, TicketCloseView
        self.add_view(TicketPanelView())
        self.add_view(TicketCloseView())

        await self._sync_commands()

    async def _sync_commands(self):
        if config.DEV_GUILD_ID:
            # Fast local sync during development - changes show up
            # almost instantly on a single test server.
            guild = discord.Object(id=config.DEV_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %d commands to dev guild %s", len(synced), config.DEV_GUILD_ID)
        else:
            # Global sync so the bot works correctly on every server
            # it's invited to, not just one hardcoded guild.
            synced = await self.tree.sync()
            log.info("Synced %d commands globally", len(synced))

    async def on_ready(self):
        log.info("Logged in as %s (id=%s)", self.user, self.user.id)
        log.info("Connected to %d guild(s)", len(self.guilds))

    async def on_disconnect(self):
        log.warning("Bot disconnected from Discord")

    async def on_resumed(self):
        log.info("Bot session resumed")

    async def on_guild_join(self, guild: discord.Guild):
        log.info("Joined new guild: %s (id=%s)", guild.name, guild.id)

    async def on_error(self, event_method, *args, **kwargs):
        # Catches any unhandled exception in an event listener so it
        # gets logged instead of silently vanishing or crashing the loop.
        log.exception("Unhandled exception in event: %s", event_method)


bot = RaidBot()


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """
    Central handler for every slash command error. Without this, a raised
    exception in a command just fails silently for the user and only
    shows up as a stack trace in the console.
    """

    if isinstance(error, app_commands.MissingPermissions):
        message = "You don't have permission to do that."
    elif isinstance(error, app_commands.CommandOnCooldown):
        message = f"That command is on cooldown. Try again in {error.retry_after:.1f}s."
    elif isinstance(error, app_commands.CheckFailure):
        message = "You can't use that command here."
    else:
        log.exception(
            "Unhandled app command error in /%s",
            interaction.command.qualified_name if interaction.command else "unknown",
            exc_info=error,
        )
        message = "Something went wrong running that command. The issue has been logged."

    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except discord.HTTPException:
        # If we can't even send the error message, there's nothing more
        # we can do - just make sure it's in the logs.
        log.warning("Failed to deliver error message to user for a failed command")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    # Handles errors from traditional "!" prefix commands, if any exist.
    if isinstance(error, commands.CommandNotFound):
        return

    log.exception("Unhandled prefix command error", exc_info=error)


async def main():
    if not config.DISCORD_TOKEN:
        log.critical("DISCORD_TOKEN is not set. Add it to your .env file and try again.")
        sys.exit(1)

    async with bot:
        initialize_database()

        try:
            await bot.start(config.DISCORD_TOKEN)
        except discord.LoginFailure:
            log.critical("Login failed - check that DISCORD_TOKEN is correct.")
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutdown requested, exiting.")
