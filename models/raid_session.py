from models.raid_member import RaidMember

# Role caps for each supported raid size - the single source of truth
# for both initial creation and later resizing, so the two can never
# drift out of sync with each other.
ROLE_CAPS = {
    8: (2, 2, 4),
    16: (2, 4, 10),
}


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
        self.max_tanks, self.max_healers, self.max_dps = ROLE_CAPS.get(raid_size, ROLE_CAPS[8])

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

        # Message IDs of reminder pings (24h/30m/start) sent to the raid
        # channel, so they can be cleaned up alongside the board once the
        # raid auto-deletes.
        self.reminder_message_ids: list[int] = []

    def resize(self, raid_size: int):
        self.raid_size = raid_size
        self.max_tanks, self.max_healers, self.max_dps = ROLE_CAPS.get(raid_size, ROLE_CAPS[8])

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