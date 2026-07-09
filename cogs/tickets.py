import logging

import discord
from discord import app_commands
from discord.ext import commands

from services.permission_service import PermissionService
from views.ticket_views import TicketPanelView

log = logging.getLogger(__name__)


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ticket = app_commands.Group(
        name="ticket",
        description="Support ticket management",
    )

    @ticket.command(name="panel", description="Post the 'Open Ticket' button in this channel")
    async def panel(self, interaction: discord.Interaction):
        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message(
                "❌ Only raid officers can post the ticket panel.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🎫 Need Help?",
            description="Click below to open a private ticket. Only you and the officers will be able to see it.",
            color=discord.Color.blurple(),
        )

        await interaction.response.send_message(embed=embed, view=TicketPanelView())


async def setup(bot):
    await bot.add_cog(Tickets(bot))
