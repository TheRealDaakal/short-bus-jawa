import asyncio
import logging

import discord

from services import guild_settings_service, ticket_service
from services.permission_service import PermissionService

log = logging.getLogger(__name__)


def _ticket_overwrites(guild: discord.Guild, opener: discord.Member) -> dict:
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        opener: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }

    for role_id in guild_settings_service.get_officer_roles(guild.id):
        role = guild.get_role(role_id)
        if role is not None:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
            )

    return overwrites


class TicketPanelView(discord.ui.View):
    """
    Persistent view (timeout=None) posted once via /ticket panel. Must be
    re-registered with bot.add_view() on every startup so the button still
    works on old messages after a restart.
    """

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Open Ticket", style=discord.ButtonStyle.blurple, custom_id="ticket_panel_open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        category_id = guild_settings_service.get_ticket_category(interaction.guild_id)

        if category_id is None:
            await interaction.response.send_message(
                "⚠️ Tickets aren't set up yet - ask an officer to run /settings ticketcategory.",
                ephemeral=True,
            )
            return

        category = interaction.guild.get_channel(category_id)

        if category is None:
            await interaction.response.send_message(
                "⚠️ The configured ticket category no longer exists - ask an officer to set a new one.",
                ephemeral=True,
            )
            return

        existing = ticket_service.get_open_ticket_for_user(interaction.guild_id, interaction.user.id)
        if existing:
            channel = interaction.guild.get_channel(existing["channel_id"])
            if channel is not None:
                await interaction.response.send_message(
                    f"You already have an open ticket: {channel.mention}",
                    ephemeral=True,
                )
                return

        await interaction.response.defer(ephemeral=True)

        channel_name = f"ticket-{interaction.user.name}"[:90].lower()

        try:
            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=_ticket_overwrites(interaction.guild, interaction.user),
                reason=f"Ticket opened by {interaction.user}",
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to create channels in that category.",
                ephemeral=True,
            )
            return

        ticket_id = ticket_service.create_ticket(interaction.guild_id, ticket_channel.id, interaction.user.id)

        embed = discord.Embed(
            title=f"🎫 Ticket #{ticket_id}",
            description=(
                f"Thanks for reaching out, {interaction.user.mention}! "
                f"Describe your issue and an officer will be with you shortly."
            ),
            color=discord.Color.blurple(),
        )
        await ticket_channel.send(embed=embed, view=TicketCloseView())

        await interaction.followup.send(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)


class TicketCloseView(discord.ui.View):
    """Persistent view attached to every ticket channel's opening message."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = ticket_service.get_ticket_by_channel(interaction.channel_id)

        if ticket is None:
            await interaction.response.send_message("This isn't a ticket channel.", ephemeral=True)
            return

        if ticket["status"] == "closed":
            await interaction.response.send_message("This ticket is already closed.", ephemeral=True)
            return

        is_opener = interaction.user.id == ticket["opened_by"]
        is_staff = PermissionService.is_officer(interaction.user)

        if not (is_opener or is_staff):
            await interaction.response.send_message(
                "Only the ticket opener or an officer can close this.",
                ephemeral=True,
            )
            return

        ticket_service.close_ticket(ticket["id"], interaction.user.id)

        await interaction.response.send_message(
            f"🔒 Ticket closed by {interaction.user.mention}. Deleting this channel in 5 seconds..."
        )

        await asyncio.sleep(5)

        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except discord.HTTPException:
            log.exception("Failed to delete ticket channel %s", interaction.channel_id)
