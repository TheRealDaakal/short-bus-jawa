from models.raid_member import RaidMember


class RaidSession:
    def __init__(
        self,
        operation,
        difficulty="",
        raid_date="",
        raid_time="",
        raid_leader="",
        raid_leader_id=None,
        raid_id=None,
        faction="Empire",
        raid_size=8,
        raid_timestamp=None,
        raid_end_timestamp=None,
        raid_timezone="",
    ):
        self.raid_id = raid_id

        self.operation = operation
        self.difficulty = difficulty
        self.raid_date = raid_date
        self.raid_time = raid_time
        self.raid_timestamp = raid_timestamp
        self.raid_end_timestamp = raid_end_timestamp
        self.raid_timezone = raid_timezone

        self.raid_leader = raid_leader
        self.raid_leader_id = raid_leader_id

        # -------------------------
        # Raid Status
        # -------------------------

        self.locked = False
        self.completed = False

        # -------------------------
        # Discord Message Tracking
        # -------------------------

        self.message = None
        self.message_id = None
        self.channel_id = None

        # -------------------------
        # Raid Configuration
        # -------------------------

        self.faction = faction
        self.raid_size = raid_size

        if raid_size == 8:
            self.max_tanks = 2
            self.max_healers = 2
            self.max_dps = 4
        else:
            self.max_tanks = 2
            self.max_healers = 4
            self.max_dps = 10

        # -------------------------
        # Raid Members
        # -------------------------

        self.tanks: list[RaidMember] = []
        self.healers: list[RaidMember] = []
        self.dps: list[RaidMember] = []
        self.bench: list[RaidMember] = []
        self.floaters: list[RaidMember] = []

        # -------------------------
        # Reminder Tracking
        # -------------------------
        # Which automated reminders/actions have already fired for this
        # raid, so the scheduler doesn't send them twice. Values used:
        # "24h", "30m", "start", "deleted".
        self.reminders_sent: set[str] = set()

    def remove_player(self, user_id: int):

        self.tanks = [
            player for player in self.tanks
            if player.id != user_id
        ]

        self.healers = [
            player for player in self.healers
            if player.id != user_id
        ]

        self.dps = [
            player for player in self.dps
            if player.id != user_id
        ]

        self.bench = [
            player for player in self.bench
            if player.id != user_id
        ]

        self.floaters = [
            player for player in self.floaters
            if player.id != user_id
        ]