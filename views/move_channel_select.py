import logging

import discord

from services.raid_manager import RaidManager
from utils.banners import attach_banner
from utils.embed_builder import build_raid_board_embed

log = logging.getLogger(__name__)


class MoveChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, raid_id: int):
        super().__init__(
            placeholder="Select the new channel for this raid...",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text],
        )

        self.raid_id = raid_id

    async def callback(self, interaction: discord.Interaction):
        from views.raid_view import RaidView

        session = RaidManager.get_session(self.raid_id)

        if session is None:
            await interaction.response.edit_message(
                content="⚠️ This raid's live data is no longer available.",
                view=None,
            )
            return

        new_channel = self.values[0]

        embed = build_raid_board_embed(session)
        banner_file = attach_banner(embed, session.operation)

        send_kwargs = {"embed": embed, "view": RaidView(self.raid_id)}
        if banner_file is not None:
            send_kwargs["file"] = banner_file

        try:
            new_message = await new_channel.send(**send_kwargs)
        except discord.Forbidden:
            await interaction.response.edit_message(
                content=f"❌ I don't have permission to post in {new_channel.mention}.",
                view=None,
            )
            return

        old_channel_id = session.channel_id
        old_message_id = session.message_id

        session.message = new_message
        session.message_id = new_message.id
        session.channel_id = new_channel.id

        old_channel = interaction.guild.get_channel(old_channel_id) if old_channel_id else None

        if old_channel is not None and old_message_id:
            try:
                old_message = await old_channel.fetch_message(old_message_id)
                await old_message.delete()
            except discord.NotFound:
                pass
            except discord.HTTPException:
                log.exception("Failed to delete old raid board after moving raid #%s", self.raid_id)

        await interaction.response.edit_message(
            content=f"✅ Raid moved to {new_channel.mention}. [Jump to it]({new_message.jump_url})",
            view=None,
        )


class MoveChannelView(discord.ui.View):
    def __init__(self, raid_id: int):
        super().__init__(timeout=120)

        self.add_item(MoveChannelSelect(raid_id))
