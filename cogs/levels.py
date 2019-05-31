import discord
import asyncio
import asyncpg

from discord.ext import commands


class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addlevel(self, ctx, playerid, lvl):
        playerid = int(playerid)
        lvl = int(lvl)

        await self.bot.db.execute('''
        UPDATE player
        SET level = $1
        WHERE player.id = $2''', lvl, playerid)


def setup(bot):
    bot.add_cog(Level(bot))
