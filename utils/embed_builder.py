import discord

from utils.constants import EMOJIS


def build_raid_embed(session):

    embed = discord.Embed(
        title="🎡 SWTOR Operations Wheel",
        description=f"# ⭐ {session.operation} ⭐",
        color=discord.Color.orange()
    )

    tanks = "\n".join(f"• {p.display_name}" for p in session.tanks)
    healers = "\n".join(f"• {p.display_name}" for p in session.healers)
    dps = "\n".join(f"• {p.display_name}" for p in session.dps)
    bench = "\n".join(f"• {p.display_name}" for p in session.bench)

    embed.add_field(
        name=f"{EMOJIS['tank']} Tanks ({len(session.tanks)}/2)",
        value=tanks if tanks else "• Empty",
        inline=True
    )

    embed.add_field(
        name=f"{EMOJIS['healer']} Healers ({len(session.healers)}/2)",
        value=healers if healers else "• Empty",
        inline=True
    )

    embed.add_field(
        name=f"{EMOJIS['dps']} DPS ({len(session.dps)}/4)",
        value=dps if dps else "• Empty",
        inline=True
    )

    embed.add_field(
        name=f"{EMOJIS['bench']} Bench ({len(session.bench)})",
        value=bench if bench else "• Empty",
        inline=False
    )

    embed.set_footer(text="Short Bus Raid Manager")

    return embed