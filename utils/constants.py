ROLE_LIMITS = {
    "tank": 2,
    "healer": 2,
    "dps": 4,
}

EMOJIS = {
    "tank": "🛡",
    "healer": "⚕️",
    "dps": "💥",
    "bench": "🪑",
    "floater": "🌊",
}

CLEANUP_MESSAGES = [
    "🚌 The Short Bus has left the station...",
    "🚌 Another successful raid. Time to go home!",
    "🚌 Jawa cleanup crew has arrived.",
    "🚌 Thanks for riding the Short Bus!",
]

# (display label, minutes)
RAID_DURATIONS = [
    ("1 hour", 60),
    ("1.5 hours", 90),
    ("2 hours", 120),
    ("2.5 hours", 150),
    ("3 hours", 180),
    ("4 hours", 240),
]

DEFAULT_RAID_DURATION_MINUTES = 120

# How long after the raid *ends* the board auto-deletes.
AUTO_DELETE_GRACE_MINUTES = 30