"""
A curated list of timezones common among gaming guilds, plus a helper to
turn a plain-English date/time + timezone into a Unix timestamp for
Discord's <t:...> auto-localizing timestamp format.
"""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# (display label, IANA timezone name)
COMMON_TIMEZONES = [
    ("Eastern (US)", "America/New_York"),
    ("Central (US)", "America/Chicago"),
    ("Mountain (US)", "America/Denver"),
    ("Pacific (US)", "America/Los_Angeles"),
    ("UK / Ireland", "Europe/London"),
    ("Central Europe", "Europe/Berlin"),
    ("Eastern Europe", "Europe/Helsinki"),
    ("Australia (Eastern)", "Australia/Sydney"),
    ("Australia (Central)", "Australia/Adelaide"),
    ("Australia (Western)", "Australia/Perth"),
    ("UTC", "UTC"),
]


class InvalidRaidDateTime(ValueError):
    pass


def to_unix_timestamp(raid_date: str, raid_time: str, tz_name: str) -> int:
    """
    Converts a raid's date ("07/10/2026"), time ("7:30 PM"), and IANA
    timezone name into a Unix timestamp suitable for Discord's <t:...>
    formatting, which auto-renders in every viewer's own local time.
    """

    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        raise InvalidRaidDateTime(f"Unknown timezone '{tz_name}'.")

    try:
        naive = datetime.strptime(f"{raid_date} {raid_time}", "%m/%d/%Y %I:%M %p")
    except ValueError:
        raise InvalidRaidDateTime(
            f"Couldn't combine date '{raid_date}' and time '{raid_time}'."
        )

    localized = naive.replace(tzinfo=tz)

    return int(localized.timestamp())
