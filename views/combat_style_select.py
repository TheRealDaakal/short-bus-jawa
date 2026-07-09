import discord

from services.raid_manager import RaidManager
from utils.swtor_data import COMBAT_STYLES
from views.discipline_select import DisciplineView


class CombatStyleSelect(discord.ui.Select):
    def __init__(self, raid_id: int, role: str):

        self.raid_id = raid_id
        self.role = role

        options = [
            discord.SelectOption(
                label=style,
                value=style,
            )
            for style in COMBAT_STYLES[role].keys()
        ]

        super().__init__(
            placeholder=f"Choose a {role} Combat Style...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):

        combat_style = self.values[0]

        # Tank and Healer combat styles each map to exactly one discipline
        # (e.g. Juggernaut tank is always Immortal), so there's nothing to
        # ask - sign up immediately instead of showing a redundant select.
        if self.role in ("Tank", "Healer"):
            await self._join_directly(interaction, combat_style)
            return

        await interaction.response.edit_message(
            content="Choose your Discipline",
            view=DisciplineView(
                raid_id=self.raid_id,
                role=self.role,
                combat_style=combat_style,
            ),
        )

    async def _join_directly(self, interaction: discord.Interaction, combat_style: str):

        discipline = COMBAT_STYLES[self.role][combat_style][0]

        session = RaidManager.get_session(self.raid_id)

        if session is None:
            await interaction.response.edit_message(
                content="Raid session not found.",
                view=None,
            )
            return

        if self.role == "Tank":
            success = RaidManager.join_tank(
                session=session,
                user=interaction.user,
                combat_style=combat_style,
                discipline=discipline,
            )
        else:
            success = RaidManager.join_healer(
                session=session,
                user=interaction.user,
                combat_style=combat_style,
                discipline=discipline,
            )

        if not success:
            await interaction.response.edit_message(
                content="That role is already full or the raid is locked.",
                view=None,
            )
            return

        await RaidManager.refresh_board(session)

        await interaction.response.edit_message(
            content=f"✅ You signed up as\n**{combat_style} • {discipline}**",
            view=None,
        )


class CombatStyleView(discord.ui.View):
    def __init__(self, raid_id: int, role: str):
        super().__init__(timeout=120)

        self.add_item(
            CombatStyleSelect(
                raid_id=raid_id,
                role=role,
            )
        )