from datetime import time

import discord

from utils.wizard_embed_builder import build_wizard_embed

# (label, 24-hour value)
_HOUR_OPTIONS = []
for _h in range(24):
    _display = _h % 12 or 12
    _suffix = "AM" if _h < 12 else "PM"
    _HOUR_OPTIONS.append((f"{_display} {_suffix}", _h))

_MINUTE_OPTIONS = (0, 15, 30, 45)


class HourSelect(discord.ui.Select):
    def __init__(self, session):
        options = [
            discord.SelectOption(label=label, value=str(hour24), default=(session.wizard_hour == hour24))
            for label, hour24 in _HOUR_OPTIONS
        ]

        super().__init__(placeholder="Hour...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        session = view.session

        session.wizard_hour = int(self.values[0])

        await _advance_if_ready(interaction, view, session)


class MinuteSelect(discord.ui.Select):
    def __init__(self, session):
        options = [
            discord.SelectOption(label=f":{minute:02d}", value=str(minute), default=(session.wizard_minute == minute))
            for minute in _MINUTE_OPTIONS
        ]

        super().__init__(placeholder="Minute...", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        session = view.session

        session.wizard_minute = int(self.values[0])

        await _advance_if_ready(interaction, view, session)


async def _advance_if_ready(interaction: discord.Interaction, view, session):
    if session.wizard_hour is None or session.wizard_minute is None:
        view.refresh()
        await interaction.response.edit_message(embed=build_wizard_embed(session), view=view)
        return

    chosen = time(hour=session.wizard_hour, minute=session.wizard_minute)

    session.raid_time = chosen.strftime("%I:%M %p").lstrip("0")
    session.wizard_hour = None
    session.wizard_minute = None
    session.step = 7

    view.refresh()
    await interaction.response.edit_message(embed=build_wizard_embed(session), view=view)
