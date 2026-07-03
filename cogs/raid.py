import random

import discord
from discord import app_commands
from discord.ext import commands

from models.raid_session import RaidSession
from views.raid_view import RaidView
from utils.embed_builder import build_raid_embed
from utils.constants import OPERATIONS

print(">>> raid.py loaded <<<")


class Raid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="raid",
        description="Spin the SWTOR Operations Wheel"
    )
    async def raid(self, interaction: discord.Interaction):

        operation = random.choice(OPERATIONS)

        session = RaidSession(operation)

        view = RaidView(session)

        await interaction.response.send_message(
            embed=build_raid_embed(session),
            view=view
        )


async def setup(bot):
    await bot.add_cog(Raid(bot))