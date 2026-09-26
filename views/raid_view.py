import logging

import discord
from discord.ui import DynamicItem, View, Button

from services.raid_manager import RaidManager
from services.permission_service import PermissionService
from utils.embed_builder import build_raid_board_embed
from views.combat_style_select import CombatStyleView

log = logging.getLogger(__name__)


async def _require_session(interaction: discord.Interaction, raid_id: int):
    """
    Every raid board button is a DynamicItem (see below) so it keeps
    working on messages posted before the current process started - but
    that means there's no bound RaidView.interaction_check to rely on,
    since dynamic items are matched by custom_id alone, not by the
    original view instance. Each button must call this first instead.

    In-memory raid state (RaidManager.active_raids) doesn't survive a
    bot restart, so this is also what tells a user their old raid board
    needs to be recreated.
    """

    session = RaidManager.get_session(raid_id)

    if session is None:
        await interaction.response.send_message(
            "⚠️ This raid's live data is no longer available - this can happen after "
            "a bot restart. Please ask an officer to create a new raid board.",
            ephemeral=True,
        )

    return session


class RaidView(View):
    def __init__(self, raid_id: int):
        super().__init__(timeout=None)

        self.raid_id = raid_id

        session = RaidManager.get_session(raid_id)
        locked = session.locked if session is not None else False

        self.add_item(TankButton(raid_id))
        self.add_item(HealerButton(raid_id))
        self.add_item(DpsButton(raid_id))
        self.add_item(BenchButton(raid_id))
        self.add_item(FloaterButton(raid_id))
        self.add_item(LeaveButton(raid_id))
        self.add_item(LockButton(raid_id, locked))
        self.add_item(FinishButton(raid_id))
        self.add_item(EditRaidButton(raid_id))
        self.add_item(MoveChannelButton(raid_id))
        self.add_item(ResizeButton(raid_id))


# -------------------------
# Signups
# -------------------------

class TankButton(DynamicItem[Button], template=r"raid_tank:(?P<raid_id>[0-9]+)"):
    def __init__(self, raid_id: int):
        super().__init__(
            Button(label="🛡 Tank", style=discord.ButtonStyle.blurple, row=0, custom_id=f"raid_tank:{raid_id}")
        )
        self.raid_id = raid_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["raid_id"]))

    async def callback(self, interaction: discord.Interaction):
        if await _require_session(interaction, self.raid_id) is None:
            return

        await interaction.response.send_message(
            "Choose your Combat Style",
            view=CombatStyleView(raid_id=self.raid_id, role="Tank"),
            ephemeral=True,
        )


class HealerButton(DynamicItem[Button], template=r"raid_healer:(?P<raid_id>[0-9]+)"):
    def __init__(self, raid_id: int):
        super().__init__(
            Button(label="⚕️ Healer", style=discord.ButtonStyle.green, row=0, custom_id=f"raid_healer:{raid_id}")
        )
        self.raid_id = raid_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["raid_id"]))

    async def callback(self, interaction: discord.Interaction):
        if await _require_session(interaction, self.raid_id) is None:
            return

        await interaction.response.send_message(
            "Choose your Combat Style",
            view=CombatStyleView(raid_id=self.raid_id, role="Healer"),
            ephemeral=True,
        )


class DpsButton(DynamicItem[Button], template=r"raid_dps:(?P<raid_id>[0-9]+)"):
    def __init__(self, raid_id: int):
        super().__init__(
            Button(label="⚔️ DPS", style=discord.ButtonStyle.red, row=0, custom_id=f"raid_dps:{raid_id}")
        )
        self.raid_id = raid_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["raid_id"]))

    async def callback(self, interaction: discord.Interaction):
        if await _require_session(interaction, self.raid_id) is None:
            return

        await interaction.response.send_message(
            "Choose your Combat Style",
            view=CombatStyleView(raid_id=self.raid_id, role="DPS"),
            ephemeral=True,
        )


class BenchButton(DynamicItem[Button], template=r"raid_bench:(?P<raid_id>[0-9]+)"):
    def __init__(self, raid_id: int):
        super().__init__(
            Button(label="🪑 Bench", style=discord.ButtonStyle.secondary, row=1, custom_id=f"raid_bench:{raid_id}")
        )
        self.raid_id = raid_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["raid_id"]))

    async def callback(self, interaction: discord.Interaction):
        session = await _require_session(interaction, self.raid_id)
        if session is None:
            return

        RaidManager.join_bench(session, interaction.user)

        await interaction.response.edit_message(
            embed=build_raid_board_embed(session),
            view=RaidView(self.raid_id),
        )


class FloaterButton(DynamicItem[Button], template=r"raid_floater:(?P<raid_id>[0-9]+)"):
    def __init__(self, raid_id: int):
        super().__init__(
            Button(label="🌊 Floater", style=discord.ButtonStyle.secondary, row=1, custom_id=f"raid_floater:{raid_id}")
        )
        self.raid_id = raid_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["raid_id"]))

    async def callback(self, interaction: discord.Interaction):
        session = await _require_session(interaction, self.raid_id)
        if session is None:
            return

        success = RaidManager.join_floater(session, interaction.user)

        if not success:
            await interaction.response.send_message(
                "The raid is already full or locked.",
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(
            embed=build_raid_board_embed(session),
            view=RaidView(self.raid_id),
        )


class LeaveButton(DynamicItem[Button], template=r"raid_leave:(?P<raid_id>[0-9]+)"):
    def __init__(self, raid_id: int):
        super().__init__(
            Button(label="❌ Leave", style=discord.ButtonStyle.gray, row=1, custom_id=f"raid_leave:{raid_id}")
        )
        self.raid_id = raid_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["raid_id"]))

    async def callback(self, interaction: discord.Interaction):
        session = await _require_session(interaction, self.raid_id)
        if session is None:
            return

        RaidManager.leave(session, interaction.user)

        await interaction.response.edit_message(
            embed=build_raid_board_embed(session),
            view=RaidView(self.raid_id),
        )


# -------------------------
# Officer Controls
# -------------------------

class LockButton(DynamicItem[Button], template=r"raid_lock:(?P<raid_id>[0-9]+)"):
    def __init__(self, raid_id: int, locked: bool = False):
        label = "🔓 Unlock" if locked else "🔒 Lock"
        super().__init__(
            Button(label=label, style=discord.ButtonStyle.danger, row=2, custom_id=f"raid_lock:{raid_id}")
        )
        self.raid_id = raid_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["raid_id"]))

    async def callback(self, interaction: discord.Interaction):
        session = await _require_session(interaction, self.raid_id)
        if session is None:
            return

        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message(
                "❌ Only raid officers can lock or unlock this raid.",
                ephemeral=True,
            )
            return

        if session.locked:
            RaidManager.unlock_raid(session)
        else:
            RaidManager.lock_raid(session)

        await interaction.response.edit_message(
            embed=build_raid_board_embed(session),
            view=RaidView(self.raid_id),
        )


class FinishButton(DynamicItem[Button], template=r"raid_finish:(?P<raid_id>[0-9]+)"):
    def __init__(self, raid_id: int):
        super().__init__(
            Button(label="🏁 Finish", style=discord.ButtonStyle.primary, row=2, custom_id=f"raid_finish:{raid_id}")
        )
        self.raid_id = raid_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["raid_id"]))

    async def callback(self, interaction: discord.Interaction):
        session = await _require_session(interaction, self.raid_id)
        if session is None:
            return

        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message(
                "❌ Only raid officers can finish this raid.",
                ephemeral=True,
            )
            return

        RaidManager.finish_raid(self.raid_id)

        await interaction.response.edit_message(
            embed=build_raid_board_embed(session),
            view=RaidView(self.raid_id),
        )


class EditRaidButton(DynamicItem[Button], template=r"raid_edit:(?P<raid_id>[0-9]+)"):
    def __init__(self, raid_id: int):
        super().__init__(
            Button(label="✏️ Edit Raid", style=discord.ButtonStyle.secondary, row=2, custom_id=f"raid_edit:{raid_id}")
        )
        self.raid_id = raid_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["raid_id"]))

    async def callback(self, interaction: discord.Interaction):
        if await _require_session(interaction, self.raid_id) is None:
            return

        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message(
                "❌ Only raid officers can edit this raid.",
                ephemeral=True,
            )
            return

        from views.edit_raid_modal import EditRaidModal

        await interaction.response.send_modal(EditRaidModal(self.raid_id))


class MoveChannelButton(DynamicItem[Button], template=r"raid_move_channel:(?P<raid_id>[0-9]+)"):
    def __init__(self, raid_id: int):
        super().__init__(
            Button(
                label="📢 Move Channel",
                style=discord.ButtonStyle.secondary,
                row=2,
                custom_id=f"raid_move_channel:{raid_id}",
            )
        )
        self.raid_id = raid_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["raid_id"]))

    async def callback(self, interaction: discord.Interaction):
        if await _require_session(interaction, self.raid_id) is None:
            return

        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message(
                "❌ Only raid officers can move this raid to a different channel.",
                ephemeral=True,
            )
            return

        from views.move_channel_select import MoveChannelView

        await interaction.response.send_message(
            "Select the channel to move this raid to:",
            view=MoveChannelView(self.raid_id),
            ephemeral=True,
        )


class ResizeButton(DynamicItem[Button], template=r"raid_resize:(?P<raid_id>[0-9]+)"):
    def __init__(self, raid_id: int):
        super().__init__(
            Button(
                label="🔁 Raid Size",
                style=discord.ButtonStyle.secondary,
                row=2,
                custom_id=f"raid_resize:{raid_id}",
            )
        )
        self.raid_id = raid_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["raid_id"]))

    async def callback(self, interaction: discord.Interaction):
        session = await _require_session(interaction, self.raid_id)
        if session is None:
            return

        if not PermissionService.is_officer(interaction.user):
            await interaction.response.send_message(
                "❌ Only raid officers can change this raid's size.",
                ephemeral=True,
            )
            return

        from views.raid_size_select import RaidSizeView

        await interaction.response.send_message(
            "Switch this raid between 8-Player and 16-Player:",
            view=RaidSizeView(self.raid_id, session.raid_size),
            ephemeral=True,
        )
