from dataclasses import dataclass


@dataclass
class RaidWizardSession:

    owner_id: int

    # -------------------------
    # Raid Configuration
    # -------------------------

    faction: str = ""
    operation: str = ""
    difficulty: str = ""

    raid_size: int = 8

    # -------------------------
    # Schedule
    # -------------------------

    raid_date: str = ""
    raid_time: str = ""

    # -------------------------
    # Leadership
    # -------------------------

    raid_leader: str = ""
    raid_leader_id: int | None = None

    # -------------------------
    # Announcements
    # -------------------------

    announcement_channel_id: int | None = None

    ping_type: str = "everyone"
    ping_role_id: int | None = None

    # -------------------------
    # Wizard Progress
    # -------------------------

    step: int = 1