import logging

import discord
from discord.ui import View, Button

from services.raid_manager import RaidManager
from services.permission_service import PermissionService
from utils.embed_builder import build_raid_board_embed
from views.combat_style_select import CombatStyleView

log = logging.getLogger(__name__)


class RaidView(View):
    def __init__(self, raid_id: int):
        super().__init__(timeout=None)

        self.raid_id = raid_id

    @property
    def session(self):
        return RaidManager.get_session(self.raid_id)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.session is None:
            await interaction.response.send_message(
                "⚠️ This raid's live data is no longer available - this can happen after "
                "a bot restart. Please ask an officer to create a new raid board.",
                ephemeral=True,
            )
            return False

        return True

    # -------------------------
    # Signups
    # -------------------------

    @discord.ui.button(label="🛡 Tank", style=discord.ButtonStyle.blurple, row=0)
    async def tank(self, interaction: discord.Interaction, button: Button):

        await interaction.response.send_message(
            "Choose your Combat Style",
            view=CombatStyleView(
                raid_id=self.raid_id,
                role="Tank",
            ),
            ephemeral=True,
        )

    @discord.ui.button(label="⚕️ Healer", style=discord.ButtonStyle.green, row=0)
    async def healer(self, interaction: discord.Interaction, button: Button):

        await interaction.response.send_message(
            "Choose your Combat Style",
            view=CombatStyleView(
                raid_id=self.raid_id,
                role="Healer",
            ),
            ephemeral=True,
        )

    @discord.ui.button(label="⚔️ DPS", style=discord.ButtonStyle.red, row=0)
    async def dps(self, interaction: discord.Interaction, button: Button):

        await interaction.response.send_message(
            "Choose your Combat Style",
            view=CombatStyleView(
                raid_id=self.raid_id,
                role="DPS",
            ),
            ephemeral=True,
        )

    @discord.ui.button(label="🪑 Bench", style=discord.ButtonStyle.secondary, row=1)
    async def bench(self, interaction: discord.Interaction, button: Button):

        RaidManager.join_bench(self.session, interaction.user)

        await interaction.response.edit_message(
            embed=build_raid_board_embed(self.session),
            view=self,
        )

    @discord.ui.button(label="🌊 Floater", style=discord.ButtonStyle.secondary, row=1)
    async def floater(self, interaction: discord.Interaction, button: Button):

        success = RaidManager.join_floater(self.session, interaction.user)

        if not success:
            await interaction.response.send_message(
                "The raid is already full or locked.",
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(
            embed=build_raid_board_embed(self.session),
            view=self,
        )

    @discord.ui.button(label="❌ Leave", style=discord.ButtonStyle.gray, row=1)
    async def leave(self, interaction: discord.Interaction, button: Button):

        RaidManager.leave(self.session, interaction.user)

        await interaction.response.edit_message(
            embed=build_raid_board_embed(self.session),
            view=self,
        )

    # -------------------------
    # Officer Controls
    # -------------------------

    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.danger, row=2)
    async def lock_toggle(self, interaction: discord.Interaction, button: Button):

        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message(
                "❌ Only raid officers can lock or unlock this raid.",
                ephemeral=True,
            )
            return

        session = self.session

        if session.locked:
            RaidManager.unlock_raid(session)
            button.label = "🔒 Lock"
        else:
            RaidManager.lock_raid(session)
            button.label = "🔓 Unlock"

        await interaction.response.edit_message(
            embed=build_raid_board_embed(session),
            view=self,
        )

    @discord.ui.button(label="🏁 Finish", style=discord.ButtonStyle.primary, row=2)
    async def finish(self, interaction: discord.Interaction, button: Button):

        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message(
                "❌ Only raid officers can finish this raid.",
                ephemeral=True,
            )
            return

        RaidManager.finish_raid(self.raid_id)

        await interaction.response.edit_message(
            embed=build_raid_board_embed(self.session),
            view=self,
        )

    @discord.ui.button(label="✏️ Edit Raid", style=discord.ButtonStyle.secondary, row=2)
    async def edit_raid(self, interaction: discord.Interaction, button: Button):

        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message(
                "❌ Only raid officers can edit this raid.",
                ephemeral=True,
            )
            return

        from views.edit_raid_modal import EditRaidModal

        await interaction.response.send_modal(EditRaidModal(self.raid_id))
