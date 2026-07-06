from models.raid_session import RaidSession
from models.raid_member import RaidMember


class RaidManager:

    bot = None

    active_raids: dict[int, RaidSession] = {}

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
    ):

        session = RaidSession(
            operation=operation,
            difficulty=difficulty,
            raid_date=raid_date,
            raid_time=raid_time,
            raid_leader=raid_leader,
            raid_leader_id=raid_leader_id,
            raid_id=raid_id,
        )

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

        session.tanks.append(
            RaidMember(
                member=user,
                combat_style=combat_style,
                discipline=discipline,
            )
        )

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

        session.healers.append(
            RaidMember(
                member=user,
                combat_style=combat_style,
                discipline=discipline,
            )
        )

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

        if len(session.dps) >= 4:
            return False

        session.dps.append(
            RaidMember(
                member=user,
                combat_style=combat_style,
                discipline=discipline,
            )
        )

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

        return True

    @classmethod
    def leave(cls, session, user):

        session.remove_player(user.id)

    # -------------------------
    # Officer Tools
    # -------------------------

    @classmethod
    def lock_raid(cls, session):

        session.locked = True

    @classmethod
    def unlock_raid(cls, session):

        session.locked = False

    @classmethod
    def finish_raid(cls, raid_id):

        session = cls.get_session(raid_id)

        if session:
            session.completed = True

    # -------------------------
    # Refresh Raid Board
    # -------------------------

    @classmethod
    async def refresh_board(cls, session):

        if session.message is None:
            return

        from utils.embed_builder import build_raid_embed
        from views.raid_view import RaidView

        await session.message.edit(
            embed=build_raid_embed(session),
            view=RaidView(session.raid_id),
        )