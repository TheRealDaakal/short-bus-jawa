from discord.ext import commands

from services.player_service import add_player


print(">>> members.py loaded <<<")


class Members(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"👋 {member} joined the server!")

        add_player(member)


async def setup(bot):
    await bot.add_cog(Members(bot))