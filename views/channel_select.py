import discord

from services.wizard_service import WizardService
from utils.wizard_embed_builder import build_wizard_embed
from views.wizard_view import WizardView


class AnnouncementChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):

        super().__init__(
            placeholder="Select the announcement channel...",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text],
        )

    async def callback(self, interaction: discord.Interaction):

        view: WizardView = self.view
        session = view.session

        channel = self.values[0]

        session.announcement_channel_id = channel.id
        session.step = 10

        view.refresh()

        await interaction.response.edit_message(
            embed=build_wizard_embed(session),
            view=view,
        )