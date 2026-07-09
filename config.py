"""
Centralized environment configuration.

Loading .env and reading os.environ happens in exactly one place so the
rest of the codebase doesn't need to know or care where config comes from.
"""

import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Optional: set this to a guild ID during development to sync slash
# commands to a single server instantly instead of waiting up to an
# hour for a global sync. Leave unset in production so the bot works
# on every server it's invited to.
DEV_GUILD_ID = os.getenv("DEV_GUILD_ID")
if DEV_GUILD_ID:
    DEV_GUILD_ID = int(DEV_GUILD_ID)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
