import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

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

        print("Loading extension...")

        await self.load_extension("cogs.raid")

        print("Extension loaded!")

        self.tree.copy_global_to(guild=guild)

        synced = await self.tree.sync(guild=guild)

        print(f"✅ Synced {len(synced)} commands")


bot = RaidBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


bot.run(TOKEN)