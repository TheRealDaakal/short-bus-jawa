import discord

from services.wizard_service import WizardService


class FactionView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=300)

        self.owner_id = owner_id

        if not WizardService.has_session(owner_id):
            WizardService.create_session(owner_id)

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:

        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Only the raid creator can use this wizard.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="🔴 Empire",
        style=discord.ButtonStyle.red,
    )
    async def empire(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        session = WizardService.get_session(self.owner_id)
        session.faction = "Empire"

        await interaction.response.send_message(
            "✅ Empire selected.\n\nOperation screen coming next.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="🔵 Republic",
        style=discord.ButtonStyle.blurple,
    )
    async def republic(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        session = WizardService.get_session(self.owner_id)
        session.faction = "Republic"

        await interaction.response.send_message(
            "✅ Republic selected.\n\nOperation screen coming next.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.gray,
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        WizardService.remove_session(self.owner_id)

        await interaction.response.edit_message(
            content="❌ Raid creation cancelled.",
            embed=None,
            view=None,
        )