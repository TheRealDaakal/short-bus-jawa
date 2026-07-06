import discord

from services.wizard_service import WizardService
from utils.wizard_embed_builder import build_wizard_embed
from views.wizard_view import WizardView


class PingTypeSelect(discord.ui.Select):
    def __init__(self):

        super().__init__(
            placeholder="Who should be pinged?",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="@everyone",
                    value="everyone",
                    emoji="📢",
                ),
                discord.SelectOption(
                    label="@here",
                    value="here",
                    emoji="📍",
                ),
                discord.SelectOption(
                    label="Raid Role",
                    value="role",
                    emoji="🎯",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction):

        view: WizardView = self.view
        session = view.session

        session.ping_type = self.values[0]
        session.step = 9

        view.refresh()

        await interaction.response.edit_message(
            embed=build_wizard_embed(session),
            view=view,
        )