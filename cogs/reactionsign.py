import discord
import asyncio
import asyncpg

from discord.ext import commands
from raidsigning import Signing


class React(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.signing = Signing(bot)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id:
            return

        if payload.message_id != 583951712625098752:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        role = discord.Object(583964043094786048)

        await member.add_roles(role, reason='Auto sign role')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not payload.guild_id:
            return
        if payload.message_id != 583951712625098752:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        role = discord.Object(583964043094786048)

        await member.remove_roles(role, reason="Remove auto sign role")


def setup(bot):
    bot.add_cog(React(bot))