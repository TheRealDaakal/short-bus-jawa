import discord
from datetime import datetime

from services.wizard_service import WizardService
from utils.wizard_embed_builder import build_wizard_embed
from views.wizard_view import WizardView


class TimeModal(discord.ui.Modal, title="Raid Time"):

    raid_time = discord.ui.TextInput(
        label="Raid Time",
        placeholder="7:30 PM",
        required=True,
        max_length=15,
    )

    def __init__(self, owner_id: int):
        super().__init__()

        self.owner_id = owner_id

    async def on_submit(self, interaction: discord.Interaction):

        raw = str(self.raid_time).strip().upper().replace(".", "")

        parsed = None
        for fmt in ("%I:%M %p", "%I %p", "%H:%M"):
            try:
                parsed = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue

        if parsed is None:
            await interaction.response.send_message(
                "⚠️ That doesn't look like a valid time. Try formats like 7:30 PM or 19:30.",
                ephemeral=True,
            )
            return

        session = WizardService.get_session(self.owner_id)

        session.raid_time = parsed.strftime("%I:%M %p").lstrip("0")
        session.step = 7

        await interaction.response.edit_message(
            embed=build_wizard_embed(session),
            view=WizardView(self.owner_id),
        )