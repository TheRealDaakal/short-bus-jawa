import calendar
from datetime import datetime

import discord

from utils.wizard_embed_builder import build_wizard_embed

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


class MonthSelect(discord.ui.Select):
    def __init__(self, session):
        options = [
            discord.SelectOption(label=name, value=str(i + 1), default=(session.wizard_month == i + 1))
            for i, name in enumerate(_MONTHS)
        ]

        super().__init__(placeholder="Month...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        session = view.session

        session.wizard_month = int(self.values[0])

        await _advance_if_ready(interaction, view, session)


class DaySelect(discord.ui.Select):
    def __init__(self, session):
        # Generous 1-31 range since the year (needed for exact days-in-
        # month) isn't known until both pieces are picked - see
        # _advance_if_ready, which clamps invalid combos like Feb 31.
        options = [
            discord.SelectOption(label=str(d), value=str(d), default=(session.wizard_day == d))
            for d in range(1, 32)
        ]

        super().__init__(placeholder="Day...", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        session = view.session

        session.wizard_day = int(self.values[0])

        await _advance_if_ready(interaction, view, session)


async def _advance_if_ready(interaction: discord.Interaction, view, session):
    if session.wizard_month is None or session.wizard_day is None:
        # Only one of the two picked so far - just reflect the choice
        # and stay on this step until both are set.
        view.refresh()
        await interaction.response.edit_message(embed=build_wizard_embed(session), view=view)
        return

    now = datetime.utcnow()
    year = now.year

    day = min(session.wizard_day, calendar.monthrange(year, session.wizard_month)[1])
    candidate = datetime(year, session.wizard_month, day)

    if candidate.date() < now.date():
        # That date already passed this year - assume they mean next year.
        year += 1
        day = min(session.wizard_day, calendar.monthrange(year, session.wizard_month)[1])
        candidate = datetime(year, session.wizard_month, day)

    session.raid_date = candidate.strftime("%m/%d/%Y")
    session.wizard_month = None
    session.wizard_day = None
    session.step = 6

    view.refresh()
    await interaction.response.edit_message(embed=build_wizard_embed(session), view=view)
