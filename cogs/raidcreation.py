import discord
import asyncio
import asyncpg

from discord.ext import commands


class Raidcreation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Raidcreation(bot))
