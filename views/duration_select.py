import discord

from services.wizard_service import WizardService
from utils.constants import RAID_DURATIONS
from utils.wizard_embed_builder import build_wizard_embed
from views.wizard_view import WizardView


class DurationSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="How long will the raid run?",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=label, value=str(minutes))
                for label, minutes in RAID_DURATIONS
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        view: WizardView = self.view
        session = view.session

        session.raid_duration_minutes = int(self.values[0])
        session.step = 8

        view.refresh()

        await interaction.response.edit_message(
            embed=build_wizard_embed(session),
            view=view,
        )
