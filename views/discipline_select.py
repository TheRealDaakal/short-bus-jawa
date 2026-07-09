import discord

from services.raid_manager import RaidManager
from utils.swtor_data import COMBAT_STYLES


class DisciplineSelect(discord.ui.Select):
    def __init__(self, raid_id: int, role: str, combat_style: str):

        self.raid_id = raid_id
        self.role = role
        self.combat_style = combat_style

        disciplines = COMBAT_STYLES[role][combat_style]

        options = [
            discord.SelectOption(
                label=discipline,
                value=discipline,
            )
            for discipline in disciplines
        ]

        super().__init__(
            placeholder="Choose your Discipline...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):

        discipline = self.values[0]

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
                combat_style=self.combat_style,
                discipline=discipline,
            )

        elif self.role == "Healer":
            success = RaidManager.join_healer(
                session=session,
                user=interaction.user,
                combat_style=self.combat_style,
                discipline=discipline,
            )

        else:
            success = RaidManager.join_dps(
                session=session,
                user=interaction.user,
                combat_style=self.combat_style,
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
            content=f"✅ You signed up as\n**{self.combat_style} • {discipline}**",
            view=None,
        )


class DisciplineView(discord.ui.View):
    def __init__(self, raid_id: int, role: str, combat_style: str):
        super().__init__(timeout=120)

        self.add_item(
            DisciplineSelect(
                raid_id=raid_id,
                role=role,
                combat_style=combat_style,
            )
        )