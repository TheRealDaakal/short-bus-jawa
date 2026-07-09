import discord

from utils.constants import EMOJIS

DIVIDER = "━━━━━━━━━━━━━━━━━━━━"


def format_role(players, limit):
    """Formats a raid role with numbered slots."""

    lines = []

    for i in range(limit):
        if i < len(players):
            lines.append(
                f"{i + 1}. {players[i].summary()}"
            )
        else:
            lines.append(
                f"{i + 1}. — Empty —"
            )

    return "\n\n".join(lines)


def build_raid_embed(session):
    return _build_raid_embed(session)


def build_raid_board_embed(session):
    """
    Builds the raid embed and points it at the content's banner image if
    one exists. Use this (not build_raid_embed directly) anywhere the
    live board gets re-rendered, so the banner never silently drops off
    after a signup, lock, or rebuild.
    """

    from utils.banners import attach_banner

    embed = _build_raid_embed(session)
    attach_banner(embed, session.operation)

    return embed


def _build_raid_embed(session):

    # ---------------------------------
    # Raid Status
    # ---------------------------------

    if getattr(session, "completed", False):
        status = "🏁 **RAID COMPLETED**"
        color = discord.Color.dark_grey()

    elif getattr(session, "locked", False):
        status = "🔴 **RAID LOCKED**"
        color = discord.Color.red()

    else:
        status = "🟢 **OPEN FOR SIGNUPS**"
        color = discord.Color.orange()

    # ---------------------------------
    # Description
    # ---------------------------------

    description = status
    description += f"\n\n# ⭐ {session.operation} ⭐"

    if session.faction:
        faction_emoji = "🔴" if session.faction == "Empire" else "🔵"
        description += f"\n{faction_emoji} **{session.faction}**"

    if session.difficulty:
        description += f"\n### ⚔ {session.difficulty}"

    description += f"\n\n{DIVIDER}"

    if session.raid_date:
        description += f"\n📅 **Date**\n{session.raid_date}"

    if session.raid_time:
        description += f"\n\n🕗 **Time**\n{session.raid_time}"

    if getattr(session, "raid_timestamp", None):
        description += f"\n<t:{session.raid_timestamp}:F> (<t:{session.raid_timestamp}:R>)"

    if getattr(session, "raid_end_timestamp", None):
        description += f"\n🏁 **Ends around** <t:{session.raid_end_timestamp}:t>"

    if session.raid_leader:
        description += f"\n\n👑 **Raid Leader**\n{session.raid_leader}"

    description += f"\n\n{DIVIDER}"

    # ---------------------------------
    # Embed
    # ---------------------------------

    embed = discord.Embed(
        title="🚌 Short Bus Jawa Raid Board",
        description=description,
        color=color,
    )

    # ---------------------------------
    # Raid Roles
    # ---------------------------------

    embed.add_field(
        name=f"{EMOJIS['tank']} Tanks ({len(session.tanks)}/{session.max_tanks})",
        value=format_role(session.tanks, session.max_tanks),
        inline=False,
    )

    embed.add_field(
        name=f"{EMOJIS['healer']} Healers ({len(session.healers)}/{session.max_healers})",
        value=format_role(session.healers, session.max_healers),
        inline=False,
    )

    embed.add_field(
        name=f"{EMOJIS['dps']} DPS ({len(session.dps)}/{session.max_dps})",
        value=format_role(session.dps, session.max_dps),
        inline=False,
    )

    # ---------------------------------
    # Bench & Floaters
    # ---------------------------------

    if session.bench:

        bench = "\n\n".join(
            f"{i + 1}. {player.summary()}"
            for i, player in enumerate(session.bench)
        )

    else:

        bench = "— Empty —"

    embed.add_field(
        name=f"{EMOJIS['bench']} Bench ({len(session.bench)})",
        value=bench,
        inline=False,
    )

    if session.floaters:

        floaters = "\n\n".join(
            f"{i + 1}. {player.summary()}"
            for i, player in enumerate(session.floaters)
        )

    else:

        floaters = "— Empty —"

    embed.add_field(
        name=f"{EMOJIS['floater']} Floaters ({len(session.floaters)})",
        value=floaters,
        inline=False,
    )

    # ---------------------------------
    # Missing Roles
    # ---------------------------------

    missing = []

    if len(session.tanks) < session.max_tanks:
        needed = session.max_tanks - len(session.tanks)
        missing.append(
            f"{EMOJIS['tank']} {needed} Tank{'s' if needed != 1 else ''}"
        )

    if len(session.healers) < session.max_healers:
        needed = session.max_healers - len(session.healers)
        missing.append(
            f"{EMOJIS['healer']} {needed} Healer{'s' if needed != 1 else ''}"
        )

    if len(session.dps) < session.max_dps:
        needed = session.max_dps - len(session.dps)
        missing.append(
            f"{EMOJIS['dps']} {needed} DPS"
        )

    if missing:

        embed.add_field(
            name="⚠️ Still Needed",
            value="\n".join(missing),
            inline=False,
        )

    else:

        embed.add_field(
            name="✅ Raid Status",
            value="🎉 Raid is Full!",
            inline=False,
        )

    # ---------------------------------
    # Footer
    # ---------------------------------

    if session.raid_id:

        embed.set_footer(
            text=f"Raid #{session.raid_id} • Short Bus Jawa v1.0"
        )

    else:

        embed.set_footer(
            text="Short Bus Jawa v1.0"
        )

    return embed