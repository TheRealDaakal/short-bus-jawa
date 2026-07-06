import discord

from models.raid_wizard_session import RaidWizardSession
from utils.constants import OPERATIONS


class OperationSelect(discord.ui.Select):
    def __init__(self, session: RaidWizardSession):

        self.session = session

        options = [
            discord.SelectOption(
                label=operation,
                value=operation,
            )
            for operation in OPERATIONS
        ]

        super().__init__(
            placeholder="Choose an Operation...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):

        self.session.operation = self.values[0]

        await interaction.response.send_message(
            f"✅ Operation selected: **{self.session.operation}**\n\n"
            "Difficulty screen coming next.",
            ephemeral=True,
        )


class OperationView(discord.ui.View):
    def __init__(self, session: RaidWizardSession):
        super().__init__(timeout=300)

        self.add_item(
            OperationSelect(session)
        )