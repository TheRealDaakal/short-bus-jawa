import discord

from services.wizard_service import WizardService
from utils.wizard_embed_builder import build_wizard_embed


class WizardView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=300)

        self.owner_id = owner_id

        if not WizardService.has_session(owner_id):
            WizardService.create_session(owner_id)

        self.refresh()

    @property
    def session(self):
        return WizardService.get_session(self.owner_id)

    def refresh(self):

        self.clear_items()

        match self.session.step:

            case 1:
                self.build_faction()

            case 2:
                self.build_operation()

            case 3:
                self.build_difficulty()

            case 4:
                self.build_raid_size()

    def build_faction(self):

        self.add_item(FactionButton("Empire"))
        self.add_item(FactionButton("Republic"))

    def build_operation(self):

        self.add_item(OperationSelect())

    def build_difficulty(self):

        self.add_item(DifficultySelect())

    def build_raid_size(self):

        self.add_item(RaidSizeButton(8))
        self.add_item(RaidSizeButton(16))


class FactionButton(discord.ui.Button):
    def __init__(self, faction: str):

        style = (
            discord.ButtonStyle.red
            if faction == "Empire"
            else discord.ButtonStyle.blurple
        )

        emoji = "🔴" if faction == "Empire" else "🔵"

        super().__init__(
            label=faction,
            emoji=emoji,
            style=style,
        )

        self.faction = faction

    async def callback(self, interaction: discord.Interaction):

        view: WizardView = self.view
        session = view.session

        session.faction = self.faction
        session.step = 2

        view.refresh()

        await interaction.response.edit_message(
            embed=build_wizard_embed(session),
            view=view,
        )


class OperationSelect(discord.ui.Select):
    def __init__(self):

        options = [
            discord.SelectOption(label="Eternity Vault"),
            discord.SelectOption(label="Karagga's Palace"),
            discord.SelectOption(label="Explosive Conflict"),
            discord.SelectOption(label="Terror From Beyond"),
            discord.SelectOption(label="Scum and Villainy"),
            discord.SelectOption(label="Dread Fortress"),
            discord.SelectOption(label="Dread Palace"),
            discord.SelectOption(label="Temple of Sacrifice"),
            discord.SelectOption(label="Gods from the Machine"),
            discord.SelectOption(label="The Nature of Progress"),
            discord.SelectOption(label="R-4 Anomaly"),
        ]

        super().__init__(
            placeholder="Select an Operation...",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):

        view: WizardView = self.view
        session = view.session

        session.operation = self.values[0]
        session.step = 3

        view.refresh()

        await interaction.response.edit_message(
            embed=build_wizard_embed(session),
            view=view,
        )


class DifficultySelect(discord.ui.Select):
    def __init__(self):

        super().__init__(
            placeholder="Select Difficulty...",
            options=[
                discord.SelectOption(label="Story Mode"),
                discord.SelectOption(label="Veteran Mode"),
                discord.SelectOption(label="Nightmare"),
            ],
        )

    async def callback(self, interaction: discord.Interaction):

        view: WizardView = self.view
        session = view.session

        session.difficulty = self.values[0]
        session.step = 4

        view.refresh()

        await interaction.response.edit_message(
            embed=build_wizard_embed(session),
            view=view,
        )


class RaidSizeButton(discord.ui.Button):
    def __init__(self, size: int):

        super().__init__(
            label=f"{size} Player",
            style=discord.ButtonStyle.green,
        )

        self.size = size

    async def callback(self, interaction: discord.Interaction):

        view: WizardView = self.view
        session = view.session

        session.raid_size = self.size

        await interaction.response.send_message(
            "✅ Raid size saved.\n\nReview screen is next.",
            ephemeral=True,
        )