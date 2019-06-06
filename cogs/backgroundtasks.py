import discord
import asyncio
import asyncpg

from discord.ext import tasks, commands


class Background(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autosign_add.start()

    @tasks.loop(seconds=5.0)
    async def autosign_add(self):
        print("Test")

    @autosign_add.before_loop
    async def before_autosign(self):
        print("waiting...")
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Background(bot))
