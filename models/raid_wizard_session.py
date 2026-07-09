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
    raid_timezone: str = ""
    raid_duration_minutes: int = 120

    # Scratch space while the Month/Day and Hour/Minute selects are
    # mid-pick - cleared once combined into raid_date/raid_time.
    wizard_month: int | None = None
    wizard_day: int | None = None
    wizard_hour: int | None = None
    wizard_minute: int | None = None

    # Unix timestamp (filled in later)
    raid_timestamp: int | None = None

    # -------------------------
    # Leadership
    # -------------------------

    raid_leader: str = ""
    raid_leader_id: int | None = None

    # -------------------------
    # Announcement
    # -------------------------

    announcement_channel_id: int | None = None

    ping_type: str = "everyone"
    ping_role_id: int | None = None

    # -------------------------
    # Wizard Progress
    # -------------------------

    step: int = 1