import discord

from services.raid_manager import RaidManager


class RaidSizeSelect(discord.ui.Select):
    def __init__(self, raid_id: int, current_size: int):
        self.raid_id = raid_id

        options = [
            discord.SelectOption(label="8-Player", value="8", default=(current_size == 8)),
            discord.SelectOption(label="16-Player", value="16", default=(current_size == 16)),
        ]

        super().__init__(
            placeholder="Choose the raid size...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        session = RaidManager.get_session(self.raid_id)

        if session is None:
            await interaction.response.edit_message(
                content="⚠️ This raid's live data is no longer available.",
                view=None,
            )
            return

        new_size = int(self.values[0])

        if new_size == session.raid_size:
            await interaction.response.edit_message(
                content=f"Raid is already set to **{new_size}-Player**.",
                view=None,
            )
            return

        error = RaidManager.resize_raid(session, new_size)

        if error:
            await interaction.response.edit_message(content=f"⚠️ {error}", view=None)
            return

        await RaidManager.refresh_board(session)

        await interaction.response.edit_message(
            content=f"✅ Raid switched to **{new_size}-Player**.",
            view=None,
        )


class RaidSizeView(discord.ui.View):
    def __init__(self, raid_id: int, current_size: int):
        super().__init__(timeout=120)

        self.add_item(RaidSizeSelect(raid_id, current_size))
