import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from services.database import initialize_database

print(">>> Imported services.database successfully <<<")

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class RaidBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):
        GUILD_ID = 929365308005814352

        guild = discord.Object(id=GUILD_ID)

        print("Loading Raid Cog...")
        await self.load_extension("cogs.raid")
        print("✅ Raid Cog Loaded")

        print("Loading Members Cog...")
        await self.load_extension("cogs.members")
        print("✅ Members Cog Loaded")

        self.tree.copy_global_to(guild=guild)

        synced = await self.tree.sync(guild=guild)

        print(f"✅ Synced {len(synced)} commands")


bot = RaidBot()


@bot.event
async def on_ready():
    print(">>> on_ready fired <<<")

    initialize_database()

    print(f"Logged in as {bot.user}")


bot.run(TOKEN)