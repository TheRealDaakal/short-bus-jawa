import discord

from services.wizard_service import WizardService
from utils.wizard_embed_builder import build_wizard_embed
from views.wizard_view import WizardView


class DateModal(discord.ui.Modal, title="Raid Date"):

    raid_date = discord.ui.TextInput(
        label="Raid Date",
        placeholder="MM/DD/YYYY",
        required=True,
        max_length=10,
    )

    def __init__(self, owner_id: int):
        super().__init__()

        self.owner_id = owner_id

    async def on_submit(self, interaction: discord.Interaction):

        session = WizardService.get_session(self.owner_id)

        session.raid_date = str(self.raid_date)
        session.step = 6

        await interaction.response.edit_message(
            embed=build_wizard_embed(session),
            view=WizardView(self.owner_id),
        )