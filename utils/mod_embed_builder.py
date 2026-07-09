import discord

_ACTION_STYLE = {
    "kick": ("👢", "Kick", discord.Color.orange()),
    "ban": ("🔨", "Ban", discord.Color.red()),
    "unban": ("♻️", "Unban", discord.Color.green()),
    "timeout": ("⏱️", "Timeout", discord.Color.gold()),
    "warn": ("⚠️", "Warning", discord.Color.yellow()),
    "clearwarnings": ("🧹", "Warnings Cleared", discord.Color.blue()),
    "purge": ("🧹", "Messages Purged", discord.Color.blue()),
    "automod": ("🤖", "Automod Action", discord.Color.orange()),
    "automod_timeout": ("🤖", "Automod Timeout", discord.Color.red()),
}


def build_mod_log_embed(
    action: str,
    target: discord.abc.User,
    moderator: discord.abc.User,
    reason: str | None,
    duration_text: str | None = None,
) -> discord.Embed:

    emoji, label, color = _ACTION_STYLE.get(
        action, ("🛡️", action.title(), discord.Color.greyple())
    )

    embed = discord.Embed(
        title=f"{emoji} {label}",
        color=color,
    )

    embed.add_field(name="User", value=f"{target.mention} ({target.id})", inline=False)
    embed.add_field(name="Moderator", value=moderator.mention, inline=False)

    if duration_text:
        embed.add_field(name="Duration", value=duration_text, inline=False)

    embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)

    embed.set_thumbnail(url=target.display_avatar.url)
    embed.timestamp = discord.utils.utcnow()

    return embed
