import discord

# Fallback role names for servers that haven't configured an officer
# role with /settings officerrole yet.
OFFICER_ROLES = {
    "Raid Officer",
    "Guild Master",
    "Officer",
}


class PermissionService:

    @staticmethod
    def is_officer(member: discord.Member) -> bool:

        if member.guild_permissions.administrator:
            return True

        from services.guild_settings_service import get_officer_roles

        configured_role_ids = get_officer_roles(member.guild.id)

        if configured_role_ids:
            return any(role.id in configured_role_ids for role in member.roles)

        # No officer role configured for this server yet - fall back to
        # matching common role names so the bot is still usable out of
        # the box.
        return any(role.name in OFFICER_ROLES for role in member.roles)

    # -------------------------
    # Moderation permissions
    # -------------------------
    #
    # These deliberately check real Discord permissions rather than role
    # names, since role names vary from server to server. This is what
    # keeps the moderation module usable on any server without per-guild
    # configuration.

    @staticmethod
    def can_kick(member: discord.Member) -> bool:
        return member.guild_permissions.kick_members

    @staticmethod
    def can_ban(member: discord.Member) -> bool:
        return member.guild_permissions.ban_members

    @staticmethod
    def can_timeout(member: discord.Member) -> bool:
        return member.guild_permissions.moderate_members

    @staticmethod
    def can_warn(member: discord.Member) -> bool:
        # Warnings are lower-stakes than kick/ban; anyone who can time
        # people out or kick them is trusted enough to warn them too.
        return (
            member.guild_permissions.moderate_members
            or member.guild_permissions.kick_members
        )

    @staticmethod
    def can_manage_settings(member: discord.Member) -> bool:
        return member.guild_permissions.manage_guild

    @staticmethod
    def can_manage_messages(member: discord.Member) -> bool:
        return member.guild_permissions.manage_messages