import discord

TOTAL_STEPS = 8


def value_or_dash(value):
    if value is None:
        return "—"

    if isinstance(value, str) and value.strip() == "":
        return "—"

    return str(value)


def build_wizard_embed(session):

    titles = {
        1: "Choose your Faction",
        2: "Choose the Operation",
        3: "Choose the Difficulty",
        4: "Choose Raid Size",
        5: "Choose Date & Time",
        6: "Choose Announcement Channel",
        7: "Choose Ping Type",
        8: "Review & Create Raid",
    }

    descriptions = {
        1: "Select whether this raid is for the Empire or Republic.",
        2: "Select the operation to run.",
        3: "Select the raid difficulty.",
        4: "Choose whether this is an 8-player or 16-player raid.",
        5: "Set the raid date and start time.",
        6: "Choose which channel will receive raid announcements.",
        7: "Choose who should be notified.",
        8: "Everything look good? Click **Create Raid**.",
    }

    embed = discord.Embed(
        title="🚌 Short Bus Jawa Raid Wizard",
        color=discord.Color.orange(),
    )

    embed.description = (
        f"## Step {session.step} of {TOTAL_STEPS}\n\n"
        f"### {titles[session.step]}\n\n"
        f"{descriptions[session.step]}"
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
            f"{value_or_dash(session.raid_time)}"
        ),
        inline=False,
    )

    channel = (
        f"<#{session.announcement_channel_id}>"
        if session.announcement_channel_id
        else "—"
    )

    if session.ping_type == "everyone":
        ping = "@everyone"
    elif session.ping_type == "here":
        ping = "@here"
    elif session.ping_type == "role":
        ping = "Raid Role"
    else:
        ping = "—"

    embed.add_field(
        name="📣 Announcement",
        value=(
            f"**Channel**\n"
            f"{channel}\n\n"

            f"**Ping**\n"
            f"{ping}"
        ),
        inline=False,
    )

    embed.set_footer(
        text=f"Short Bus Jawa • Step {session.step}/{TOTAL_STEPS}"
    )

    return embed