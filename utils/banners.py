"""
Maps SWTOR content names (Operations/Lair Bosses) to local banner image
files in assets/banners/, and attaches them to raid board embeds.

To add a banner: drop an image named after the content's slug into
assets/banners/ (see slugify() for the exact naming rule) and it will be
picked up automatically - no code changes needed.
"""

from pathlib import Path

import discord

BANNER_DIR = Path("assets") / "banners"

_SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


def slugify(name: str) -> str:
    """
    Converts a content name into the filename (minus extension) the bot
    looks for, e.g. "Eternity Vault" -> "eternity_vault",
    "R-4 Anomaly" -> "r_4_anomaly".
    """

    slug = name.lower().strip()
    slug = slug.replace("'", "")

    cleaned = []
    for char in slug:
        if char.isalnum():
            cleaned.append(char)
        else:
            cleaned.append("_")

    slug = "".join(cleaned)

    while "__" in slug:
        slug = slug.replace("__", "_")

    return slug.strip("_")


def get_banner_path(content_name: str) -> Path | None:
    slug = slugify(content_name)

    for ext in _SUPPORTED_EXTENSIONS:
        path = BANNER_DIR / f"{slug}{ext}"
        if path.exists():
            return path

    return None


def get_banner_file(content_name: str) -> discord.File | None:
    """Returns a fresh discord.File for this content's banner, or None."""

    path = get_banner_path(content_name)

    if path is None:
        return None

    return discord.File(path, filename=path.name)


def attach_banner(embed: discord.Embed, content_name: str) -> discord.File | None:
    """
    If a banner exists for this content, points the embed's image at it
    and returns the discord.File that must be sent alongside the embed.
    Returns None (and leaves the embed untouched) if no banner exists.
    """

    file = get_banner_file(content_name)

    if file is None:
        return None

    embed.set_image(url=f"attachment://{file.filename}")

    return file
