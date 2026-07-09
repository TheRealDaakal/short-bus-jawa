import discord

from services.wizard_service import WizardService
from utils.timezones import COMMON_TIMEZONES
from utils.wizard_embed_builder import build_wizard_embed
from views.wizard_view import WizardView


class TimezoneSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Choose your timezone...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=label, value=tz_name)
                for label, tz_name in COMMON_TIMEZONES
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        view: WizardView = self.view
        session = view.session

        session.raid_timezone = self.values[0]
        session.step = 9

        view.refresh()

        await interaction.response.edit_message(
            embed=build_wizard_embed(session),
            view=view,
        )
