"""
The single source of truth for SWTOR Operations and Lair Bosses.

When BioWare/Broadsword ships new raid content, add ONE entry here and it
automatically shows up everywhere: the Raid Wizard's content picker, the
Operations Wheel (/raid spin), and difficulty/raid-size restrictions.
Nothing else in the codebase needs to change.

Verified current as of Game Update 7.9 "Legacy Reborn" (July 2026). The
next operation (3 bosses) is in early PTS testing for Update 8.0 and isn't
live yet - add it here once it actually ships and has a name.

Fields:
- name: display name, used as the value stored on raids
- type: "operation" (multiple bosses) or "lair_boss" (single boss). Both
  are playable at 8-man and 16-man; lair bosses just lack Master/
  Nightmare Mode by default (see story_veteran_only).
- story_veteran_only: True if this content has no Master/Nightmare Mode
"""

CONTENT = [
    # ---------------------------------
    # Operations
    # ---------------------------------
    {"name": "Eternity Vault", "type": "operation", "story_veteran_only": True},
    {"name": "Karagga's Palace", "type": "operation", "story_veteran_only": True},
    {"name": "Explosive Conflict", "type": "operation"},
    {"name": "Terror From Beyond", "type": "operation"},
    {"name": "Scum and Villainy", "type": "operation"},
    {"name": "Dread Fortress", "type": "operation"},
    {"name": "Dread Palace", "type": "operation"},
    {"name": "Temple of Sacrifice", "type": "operation", "story_veteran_only": True},
    {"name": "The Ravagers", "type": "operation", "story_veteran_only": True},
    {"name": "Gods from the Machine", "type": "operation"},
    {"name": "The Nature of Progress", "type": "operation"},
    {"name": "R-4 Anomaly", "type": "operation", "story_veteran_only": True},

    # ---------------------------------
    # Lair Bosses (single-boss operations)
    # ---------------------------------
    {"name": "Xenoanalyst II", "type": "lair_boss"},
    {"name": "The Eyeless", "type": "lair_boss"},
    {"name": "Golden Fury", "type": "lair_boss"},
    {"name": "Colossal Monolith", "type": "lair_boss"},
    {"name": "Geonosian Hive Queen", "type": "lair_boss"},
    # Got a Master/Nightmare Mode in Update 7.7 - unlike most lair bosses.
    {"name": "Relentless Replication (Propagator Core XR-53)", "type": "lair_boss", "story_veteran_only": False},
]

_BY_NAME = {entry["name"]: entry for entry in CONTENT}

DIFFICULTIES = ["Story Mode", "Veteran Mode", "Nightmare Mode"]


def all_operations() -> list[str]:
    return [entry["name"] for entry in CONTENT if entry["type"] == "operation"]


def all_lair_bosses() -> list[str]:
    return [entry["name"] for entry in CONTENT if entry["type"] == "lair_boss"]


def all_content() -> list[dict]:
    return CONTENT


def is_lair_boss(name: str) -> bool:
    entry = _BY_NAME.get(name)
    return entry is not None and entry["type"] == "lair_boss"


def available_difficulties(name: str) -> list[str]:
    """Returns the difficulties that actually exist for this content."""

    entry = _BY_NAME.get(name)

    if entry is None:
        return DIFFICULTIES

    # Lair bosses default to no Master/Nightmare Mode, but a specific
    # entry can override this with "story_veteran_only": False if that
    # boss got a harder mode added later (e.g. Relentless Replication).
    default_restricted = entry["type"] == "lair_boss"
    restricted = entry.get("story_veteran_only", default_restricted)

    if restricted:
        return ["Story Mode", "Veteran Mode"]

    return DIFFICULTIES


def available_raid_sizes(name: str) -> list[int]:
    """
    Returns the raid sizes that actually exist for this content.

    Every current lair boss (Xenoanalyst II, The Eyeless, Golden Fury,
    Colossal Monolith, Geonosian Hive Queen, Relentless Replication) is
    playable in both 8-man and 16-man Story/Veteran groups, same as
    operations - the only thing that sets lair bosses apart is the lack
    of a Master/Nightmare Mode (see available_difficulties). There is
    currently no 8-man-only content, but this stays name-keyed so a
    future exception can be added without touching any callers.
    """

    return [8, 16]
