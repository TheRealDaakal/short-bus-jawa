import discord

TOTAL_STEPS = 8


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
        8: "Review your raid before creating it.",
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
        name="Current Settings",
        value=(
            f"**Faction:** {session.faction or '—'}\n"
            f"**Operation:** {session.operation or '—'}\n"
            f"**Difficulty:** {session.difficulty or '—'}\n"
            f"**Raid Size:** {session.raid_size}-Player"
        ),
        inline=False,
    )

    embed.set_footer(text="Short Bus Jawa v1.0")

    return embed