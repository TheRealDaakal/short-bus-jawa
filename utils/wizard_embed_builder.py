import discord

TOTAL_STEPS = 11

_TITLES = {
    1: "Choose your Faction",
    2: "Choose the Operation or Lair Boss",
    3: "Choose the Difficulty",
    4: "Choose Raid Size",
    5: "Set the Raid Date",
    6: "Set the Raid Time",
    7: "How Long Will It Run?",
    8: "Choose your Timezone",
    9: "Choose Announcement Channel",
    10: "Choose Ping Type",
    11: "Review Your Raid",
}

_DESCRIPTIONS = {
    1: "Select whether this raid is for the Empire or Republic.",
    2: "Select the operation or lair boss to run.",
    3: "Select the raid difficulty.",
    4: "Choose whether this is an 8-player or 16-player raid.",
    5: "Pick the month and day below.",
    6: "Pick the hour and minute below.",
    7: "This decides when the signup board auto-deletes afterward.",
    8: "So everyone sees the raid time in their own local time, automatically.",
    9: "Choose which channel will receive the raid announcement.",
    10: "Choose who should be notified when the raid is posted.",
    11: (
        "Review every setting below.\n\n"
        "If everything looks correct, click **🚀 Create Raid**."
    ),
}


def value_or_dash(value):
    if value is None:
        return "—"

    if isinstance(value, str) and value.strip() == "":
        return "—"

    return str(value)


def _ping_label(session) -> str:
    if session.ping_type == "everyone":
        return "@everyone"
    if session.ping_type == "here":
        return "@here"
    if session.ping_type == "role":
        if session.ping_role_id:
            return f"<@&{session.ping_role_id}>"
        return "Raid Role (not configured yet)"
    if session.ping_type == "none":
        return "🔕 No Ping"
    return "—"


def _timezone_label(session) -> str:
    from utils.timezones import COMMON_TIMEZONES

    if not session.raid_timezone:
        return "—"

    for label, tz_name in COMMON_TIMEZONES:
        if tz_name == session.raid_timezone:
            return label

    return session.raid_timezone


def _duration_label(minutes: int) -> str:
    from utils.constants import RAID_DURATIONS

    for label, value in RAID_DURATIONS:
        if value == minutes:
            return label

    hours = minutes / 60
    return f"{hours:g} hours"


def _timestamp_preview(session) -> str:
    """
    Once date, time, and timezone are all set, show a live preview of the
    Discord timestamp so the raid leader can double check it before
    posting - this is exactly what everyone else will see, auto-converted
    to their own local time.
    """

    if not (session.raid_date and session.raid_time and session.raid_timezone):
        return ""

    from utils.timezones import InvalidRaidDateTime, to_unix_timestamp

    try:
        epoch = to_unix_timestamp(session.raid_date, session.raid_time, session.raid_timezone)
    except InvalidRaidDateTime:
        return ""

    end_epoch = epoch + session.raid_duration_minutes * 60

    return (
        f"\n\n**Preview**\n"
        f"Starts: <t:{epoch}:F> (<t:{epoch}:R>)\n"
        f"Ends: <t:{end_epoch}:t>"
    )


def build_wizard_embed(session):

    color = (
        discord.Color.green()
        if session.step == TOTAL_STEPS
        else discord.Color.orange()
    )

    embed = discord.Embed(
        title="🚌 Short Bus Jawa Raid Wizard",
        color=color,
    )

    embed.description = (
        f"## Step {session.step} of {TOTAL_STEPS}\n\n"
        f"### {_TITLES[session.step]}\n\n"
        f"{_DESCRIPTIONS[session.step]}"
    )

    embed.add_field(
        name="📋 Raid Details",
        value=(
            f"**Faction**\n"
            f"{value_or_dash(session.faction)}\n\n"

            f"**Operation**\n"
            f"{value_or_dash(session.operation)}\n\n"

            f"**Difficulty**\n"
            f"{value_or_dash(session.difficulty)}\n\n"

            f"**Raid Size**\n"
            f"{session.raid_size}-Player"
        ),
        inline=False,
    )

    embed.add_field(
        name="📅 Schedule",
        value=(
            f"**Date**\n"
            f"{value_or_dash(session.raid_date)}\n\n"

            f"**Time**\n"
            f"{value_or_dash(session.raid_time)}\n\n"

            f"**Duration**\n"
            f"{_duration_label(session.raid_duration_minutes)}\n\n"

            f"**Timezone**\n"
            f"{_timezone_label(session)}"
            + _timestamp_preview(session)
        ),
        inline=False,
    )

    channel = (
        f"<#{session.announcement_channel_id}>"
        if session.announcement_channel_id
        else "—"
    )

    embed.add_field(
        name="📣 Announcement",
        value=(
            f"**Channel**\n"
            f"{channel}\n\n"

            f"**Ping**\n"
            f"{_ping_label(session)}"
        ),
        inline=False,
    )

    embed.set_footer(
        text=f"Short Bus Jawa • Step {session.step}/{TOTAL_STEPS}"
    )

    return embed
