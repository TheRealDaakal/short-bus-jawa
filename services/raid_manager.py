import time

from models.raid_session import RaidSession
from models.raid_member import RaidMember


class RaidManager:

    # Set once in bot.py's setup_hook - needed by refresh_board() to look
    # up a raid's channel when a restored session has no cached Message
    # object yet.
    bot = None

    active_raids: dict[int, RaidSession] = {}

    # -------------------------
    # Persistence
    # -------------------------

    @classmethod
    def persist(cls, session):
        """
        Saves the live session's current state to the database so it
        survives a bot restart. Call this after any mutation - signups,
        lock/unlock, finish, edits, or a channel move.
        """

        from services import raid_storage

        raid_storage.save_raid_state(session)

    # -------------------------
    # Session Management
    # -------------------------

    @classmethod
    def create_session(
        cls,
        raid_id: int,
        operation: str,
        difficulty: str = "",
        raid_date: str = "",
        raid_time: str = "",
        raid_leader: str = "",
        raid_leader_id: int | None = None,
        faction: str = "Empire",
        raid_size: int = 8,
        raid_timestamp: int | None = None,
        raid_end_timestamp: int | None = None,
        raid_timezone: str = "",
    ):

        session = RaidSession(
            operation=operation,
            difficulty=difficulty,
            raid_date=raid_date,
            raid_time=raid_time,
            raid_leader=raid_leader,
            raid_leader_id=raid_leader_id,
            raid_id=raid_id,
            faction=faction,
            raid_size=raid_size,
            raid_timestamp=raid_timestamp,
            raid_end_timestamp=raid_end_timestamp,
            raid_timezone=raid_timezone,
        )

        # If this raid is being created less than 24h/30m before it
        # starts (or it's already started, like a /raid spin raid),
        # don't fire reminders/actions for thresholds already behind us.
        # This is what stops a /raid spin raid - whose "start time" is
        # essentially "now" - from being instantly auto-locked by the
        # scheduler seconds after it's posted.
        if raid_timestamp is not None:
            seconds_until_start = raid_timestamp - int(time.time())

            if seconds_until_start <= 24 * 3600:
                session.reminders_sent.add("24h")
            if seconds_until_start <= 30 * 60:
                session.reminders_sent.add("30m")
            if seconds_until_start <= 0:
                session.reminders_sent.add("start")

        cls.active_raids[raid_id] = session

        return session

    @classmethod
    def get_session(cls, raid_id):
        return cls.active_raids.get(raid_id)

    @classmethod
    def remove_session(cls, raid_id):
        cls.active_raids.pop(raid_id, None)

    # -------------------------
    # Signup Logic
    # -------------------------

    @classmethod
    def _total_signed_up(cls, session) -> int:
        """
        Tank + Healer + DPS + Floater all draw from the same 8/16-person
        pool, since a Floater can occupy a slot that would otherwise go
        to an under-filled main role. Bench is intentionally excluded -
        it's overflow beyond the raid's actual size.
        """

        return (
            len(session.tanks)
            + len(session.healers)
            + len(session.dps)
            + len(session.floaters)
        )

    @classmethod
    def join_tank(
        cls,
        session,
        user,
        combat_style="",
        discipline="",
    ):

        if session.locked:
            return False

        session.remove_player(user.id)

        if len(session.tanks) >= session.max_tanks:
            return False

        if cls._total_signed_up(session) >= session.raid_size:
            return False

        session.tanks.append(
            RaidMember(
                member=user,
                combat_style=combat_style,
                discipline=discipline,
            )
        )

        cls.persist(session)

        return True

    @classmethod
    def join_healer(
        cls,
        session,
        user,
        combat_style="",
        discipline="",
    ):

        if session.locked:
            return False

        session.remove_player(user.id)

        if len(session.healers) >= session.max_healers:
            return False

        if cls._total_signed_up(session) >= session.raid_size:
            return False

        session.healers.append(
            RaidMember(
                member=user,
                combat_style=combat_style,
                discipline=discipline,
            )
        )

        cls.persist(session)

        return True

    @classmethod
    def join_dps(
        cls,
        session,
        user,
        combat_style="",
        discipline="",
    ):

        if session.locked:
            return False

        session.remove_player(user.id)

        if len(session.dps) >= session.max_dps:
            return False

        if cls._total_signed_up(session) >= session.raid_size:
            return False

        session.dps.append(
            RaidMember(
                member=user,
                combat_style=combat_style,
                discipline=discipline,
            )
        )

        cls.persist(session)

        return True

    @classmethod
    def join_bench(
        cls,
        session,
        user,
        combat_style="",
        discipline="",
    ):

        if session.locked:
            return False

        session.remove_player(user.id)

        session.bench.append(
            RaidMember(
                member=user,
                combat_style=combat_style,
                discipline=discipline,
            )
        )

        cls.persist(session)

        return True

    @classmethod
    def join_floater(
        cls,
        session,
        user,
        combat_style="",
        discipline="",
    ):
        """
        A Floater is available to fill in wherever needed once the raid
        starts, rather than committing to a specific role up front - but
        still counts against the raid's total 8/16-person size, same as
        every other role.
        """

        if session.locked:
            return False

        session.remove_player(user.id)

        if cls._total_signed_up(session) >= session.raid_size:
            return False

        session.floaters.append(
            RaidMember(
                member=user,
                combat_style=combat_style,
                discipline=discipline,
            )
        )

        cls.persist(session)

        return True

    @classmethod
    def leave(cls, session, user):

        session.remove_player(user.id)

        cls.persist(session)

    # -------------------------
    # Officer Tools
    # -------------------------

    @classmethod
    def lock_raid(cls, session):

        session.locked = True

        cls.persist(session)

    @classmethod
    def unlock_raid(cls, session):

        session.locked = False

        cls.persist(session)

    @classmethod
    def finish_raid(cls, raid_id):

        session = cls.get_session(raid_id)

        if session:
            session.completed = True

            cls.persist(session)

    # -------------------------
    # Refresh Raid Board
    # -------------------------

    @classmethod
    async def refresh_board(cls, session):

        import discord

        message = session.message

        # A session restored from the database on startup has no cached
        # Message object yet (it's never been sent/edited by this
        # process) - fetch it once from its known channel/message ID
        # instead of silently doing nothing.
        if message is None and cls.bot is not None and session.channel_id and session.message_id:
            channel = cls.bot.get_channel(session.channel_id)

            if channel is not None:
                try:
                    message = await channel.fetch_message(session.message_id)
                    session.message = message
                except discord.HTTPException:
                    return

        if message is None:
            return

        from utils.embed_builder import build_raid_board_embed
        from views.raid_view import RaidView

        await message.edit(
            embed=build_raid_board_embed(session),
            view=RaidView(session.raid_id),
        )