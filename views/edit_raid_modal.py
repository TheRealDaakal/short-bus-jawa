import discord
from datetime import datetime

from services.raid_manager import RaidManager


class EditRaidModal(discord.ui.Modal, title="Edit Raid"):

    raid_date = discord.ui.TextInput(
        label="Raid Date",
        placeholder="MM/DD/YYYY",
        required=True,
        max_length=10,
    )

    raid_time = discord.ui.TextInput(
        label="Raid Time",
        placeholder="7:30 PM",
        required=True,
        max_length=15,
    )

    raid_leader = discord.ui.TextInput(
        label="Raid Leader",
        required=False,
        max_length=100,
    )

    def __init__(self, raid_id: int):
        super().__init__()

        self.raid_id = raid_id

        session = RaidManager.get_session(raid_id)

        if session is not None:
            self.raid_date.default = session.raid_date
            self.raid_time.default = session.raid_time
            self.raid_leader.default = session.raid_leader

    async def on_submit(self, interaction: discord.Interaction):

        session = RaidManager.get_session(self.raid_id)

        if session is None:
            await interaction.response.send_message(
                "⚠️ This raid's live data is no longer available - this can happen after "
                "a bot restart. Please ask an officer to create a new raid board.",
                ephemeral=True,
            )
            return

        raw_date = str(self.raid_date).strip()

        try:
            parsed_date = datetime.strptime(raw_date, "%m/%d/%Y")
        except ValueError:
            await interaction.response.send_message(
                "⚠️ That doesn't look like a valid date. Please use MM/DD/YYYY, e.g. 07/10/2026.",
                ephemeral=True,
            )
            return

        raw_time = str(self.raid_time).strip().upper().replace(".", "")

        parsed_time = None
        for fmt in ("%I:%M %p", "%I %p", "%H:%M"):
            try:
                parsed_time = datetime.strptime(raw_time, fmt)
                break
            except ValueError:
                continue

        if parsed_time is None:
            await interaction.response.send_message(
                "⚠️ That doesn't look like a valid time. Try formats like 7:30 PM or 19:30.",
                ephemeral=True,
            )
            return

        session.raid_date = parsed_date.strftime("%m/%d/%Y")
        session.raid_time = parsed_time.strftime("%I:%M %p").lstrip("0")

        if self.raid_leader.value.strip():
            session.raid_leader = self.raid_leader.value.strip()

        # Recompute the auto-localizing Discord timestamp to match the new
        # date/time, using whichever timezone the raid was originally
        # scheduled in - keeps the <t:...> tag in the embed truthful
        # instead of drifting from the plain-text date/time.
        if session.raid_timezone:
            from utils.timezones import InvalidRaidDateTime, to_unix_timestamp

            try:
                new_start = to_unix_timestamp(
                    session.raid_date, session.raid_time, session.raid_timezone
                )
            except InvalidRaidDateTime as e:
                await interaction.response.send_message(f"⚠️ {e}", ephemeral=True)
                return

            duration = (
                session.raid_end_timestamp - session.raid_timestamp
                if session.raid_timestamp and session.raid_end_timestamp
                else 2 * 3600
            )
            session.raid_timestamp = new_start
            session.raid_end_timestamp = new_start + duration

        await RaidManager.refresh_board(session)

        await interaction.response.send_message(
            "✅ Raid details updated.",
            ephemeral=True,
        )
