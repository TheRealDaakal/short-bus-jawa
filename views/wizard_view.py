import logging

import discord

from services.wizard_service import WizardService
from utils.wizard_embed_builder import build_wizard_embed

log = logging.getLogger(__name__)


def _ping_content(session) -> str | None:
    if session.ping_type == "everyone":
        return "@everyone"
    if session.ping_type == "here":
        return "@here"
    if session.ping_type == "role" and session.ping_role_id:
        return f"<@&{session.ping_role_id}>"
    return None


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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Only the person who started this wizard can use it.",
                ephemeral=True,
            )
            return False

        return True

    async def on_timeout(self):
        WizardService.remove_session(self.owner_id)

    def refresh(self):
        self.clear_items()

        match self.session.step:
            case 1:
                self.build_faction()
            case 2:
                self.build_content()
            case 3:
                self.build_difficulty()
            case 4:
                self.build_raid_size()
            case 5:
                self.build_date()
            case 6:
                self.build_time()
            case 7:
                self.build_duration()
            case 8:
                self.build_timezone()
            case 9:
                self.build_channel()
            case 10:
                self.build_ping()
            case 11:
                self.build_review()

        self.add_item(CancelButton())

    def build_faction(self):
        self.add_item(FactionButton("Empire"))
        self.add_item(FactionButton("Republic"))

    def build_content(self):
        self.add_item(ContentSelect())

    def build_difficulty(self):
        self.add_item(DifficultySelect(self.session.operation))

    def build_raid_size(self):
        self.add_item(RaidSizeButton(8))
        self.add_item(RaidSizeButton(16))

    def build_date(self):
        from views.date_select import MonthSelect, DaySelect
        self.add_item(MonthSelect(self.session))
        self.add_item(DaySelect(self.session))

    def build_time(self):
        from views.time_select import HourSelect, MinuteSelect
        self.add_item(HourSelect(self.session))
        self.add_item(MinuteSelect(self.session))

    def build_timezone(self):
        from views.timezone_select import TimezoneSelect
        self.add_item(TimezoneSelect())

    def build_duration(self):
        from views.duration_select import DurationSelect
        self.add_item(DurationSelect())

    def build_channel(self):
        from views.channel_select import AnnouncementChannelSelect
        self.add_item(AnnouncementChannelSelect())

    def build_ping(self):
        from views.ping_select import PingTypeSelect
        self.add_item(PingTypeSelect())

    def build_review(self):
        self.add_item(CreateRaidButton())


class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel", style=discord.ButtonStyle.gray, row=4)

    async def callback(self, interaction: discord.Interaction):
        view: WizardView = self.view

        WizardService.remove_session(view.owner_id)

        await interaction.response.edit_message(
            content="❌ Raid creation cancelled.",
            embed=None,
            view=None,
        )


class FactionButton(discord.ui.Button):
    def __init__(self, faction: str):
        super().__init__(
            label=faction,
            emoji="🔴" if faction == "Empire" else "🔵",
            style=discord.ButtonStyle.red
            if faction == "Empire"
            else discord.ButtonStyle.blurple,
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


class ContentSelect(discord.ui.Select):
    def __init__(self):
        from utils.swtor_content import all_content

        options = []
        for entry in all_content():
            options.append(
                discord.SelectOption(
                    label=entry["name"],
                    description="Lair Boss" if entry["type"] == "lair_boss" else "Operation",
                    emoji="👑" if entry["type"] == "lair_boss" else "⚔️",
                )
            )

        super().__init__(
            placeholder="Choose Operation or Lair Boss...",
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
    def __init__(self, operation: str):
        from utils.swtor_content import available_difficulties

        super().__init__(
            placeholder="Choose Difficulty...",
            options=[
                discord.SelectOption(label=difficulty)
                for difficulty in available_difficulties(operation)
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        from utils.swtor_content import available_raid_sizes

        view: WizardView = self.view
        session = view.session

        session.difficulty = self.values[0]

        # Lair bosses are always 8-man - skip the raid size step entirely
        # rather than showing a choice that doesn't apply.
        sizes = available_raid_sizes(session.operation)
        if sizes == [8]:
            session.raid_size = 8
            session.step = 5
        else:
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
        session.step = 5

        view.refresh()

        await interaction.response.edit_message(
            embed=build_wizard_embed(session),
            view=view,
        )


class CreateRaidButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="🚀 Create Raid",
            style=discord.ButtonStyle.green,
        )

    async def callback(self, interaction: discord.Interaction):
        from services.raid_poster import create_and_post_raid

        view: WizardView = self.view
        session = view.session

        missing = []
        if not session.operation:
            missing.append("Operation")
        if not session.difficulty:
            missing.append("Difficulty")
        if not session.raid_date:
            missing.append("Date")
        if not session.raid_time:
            missing.append("Time")
        if not session.raid_timezone:
            missing.append("Timezone")
        if not session.announcement_channel_id:
            missing.append("Announcement Channel")

        if missing:
            await interaction.response.send_message(
                f"⚠️ Please finish these steps first: {', '.join(missing)}.",
                ephemeral=True,
            )
            return

        channel = interaction.guild.get_channel(session.announcement_channel_id)

        if channel is None:
            await interaction.response.send_message(
                "⚠️ I can't find that announcement channel anymore - please pick a different one.",
                ephemeral=True,
            )
            return

        from utils.timezones import InvalidRaidDateTime, to_unix_timestamp

        try:
            raid_timestamp = to_unix_timestamp(
                session.raid_date, session.raid_time, session.raid_timezone
            )
        except InvalidRaidDateTime as e:
            await interaction.response.send_message(f"⚠️ {e}", ephemeral=True)
            return

        raid_end_timestamp = raid_timestamp + session.raid_duration_minutes * 60

        # Saving to the DB and posting the board can take a moment - defer
        # so Discord doesn't consider the interaction failed.
        await interaction.response.defer()

        try:
            raid_id, message = await create_and_post_raid(
                guild_id=interaction.guild_id,
                channel=channel,
                created_by=interaction.user,
                operation=session.operation,
                difficulty=session.difficulty,
                raid_date=session.raid_date,
                raid_time=session.raid_time,
                faction=session.faction or "Empire",
                raid_size=session.raid_size,
                raid_timestamp=raid_timestamp,
                raid_end_timestamp=raid_end_timestamp,
                raid_timezone=session.raid_timezone,
                content=_ping_content(session),
            )
        except discord.Forbidden:
            await interaction.followup.send(
                f"❌ I don't have permission to post in {channel.mention}.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            log.exception("Failed to post raid board")
            await interaction.followup.send(
                "❌ Failed to post the raid board. Please try again.",
                ephemeral=True,
            )
            return
        except Exception:
            log.exception("Failed to create raid")
            await interaction.followup.send(
                "❌ Something went wrong saving the raid. Please try again.",
                ephemeral=True,
            )
            return

        WizardService.remove_session(view.owner_id)

        await interaction.edit_original_response(
            content=f"✅ Raid #{raid_id} created in {channel.mention}! [Jump to it]({message.jump_url})",
            embed=None,
            view=None,
        )
