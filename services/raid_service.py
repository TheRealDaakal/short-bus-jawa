from models.raid_session import RaidSession


class RaidService:

    @staticmethod
    def join_tank(session: RaidSession, user):
        session.remove_player(user.id)

        if len(session.tanks) >= 2:
            return False

        session.tanks.append(user)
        return True

    @staticmethod
    def join_healer(session: RaidSession, user):
        session.remove_player(user.id)

        if len(session.healers) >= 2:
            return False

        session.healers.append(user)
        return True

    @staticmethod
    def join_dps(session: RaidSession, user):
        session.remove_player(user.id)

        if len(session.dps) >= 4:
            return False

        session.dps.append(user)
        return True

    @staticmethod
    def join_bench(session: RaidSession, user):
        session.remove_player(user.id)
        session.bench.append(user)
        return True

    @staticmethod
    def leave(session: RaidSession, user):
        session.remove_player(user.id)