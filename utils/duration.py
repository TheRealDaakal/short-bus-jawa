"""
Parses short duration strings like "10m", "1h", "3d" into seconds.

Supported units: s (seconds), m (minutes), h (hours), d (days).
"""

import re

_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
}

_PATTERN = re.compile(r"^(\d+)\s*([smhd])$", re.IGNORECASE)

# Discord's own cap on timeout length.
MAX_TIMEOUT_SECONDS = 28 * 24 * 60 * 60  # 28 days


class InvalidDuration(ValueError):
    pass


def parse_duration(text: str) -> int:
    """
    Parse a duration string (e.g. "10m", "2h", "1d") into seconds.

    Raises InvalidDuration if the string can't be parsed or exceeds
    Discord's 28-day timeout cap.
    """

    match = _PATTERN.match(text.strip())

    if not match:
        raise InvalidDuration(
            f"Couldn't parse duration '{text}'. Use formats like 10m, 1h, or 3d."
        )

    amount = int(match.group(1))
    unit = match.group(2).lower()

    seconds = amount * _UNIT_SECONDS[unit]

    if seconds <= 0:
        raise InvalidDuration("Duration must be greater than zero.")

    if seconds > MAX_TIMEOUT_SECONDS:
        raise InvalidDuration("Timeouts can't be longer than 28 days.")

    return seconds


def format_duration(seconds: int) -> str:
    """Human-readable form of a duration in seconds, e.g. '1h 30m'."""

    days, remainder = divmod(seconds, _UNIT_SECONDS["d"])
    hours, remainder = divmod(remainder, _UNIT_SECONDS["h"])
    minutes, secs = divmod(remainder, _UNIT_SECONDS["m"])

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs and not parts:
        parts.append(f"{secs}s")

    return " ".join(parts) if parts else "0s"
