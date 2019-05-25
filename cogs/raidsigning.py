import discord
import asyncio
import asyncpg

from discord.ext import commands
from globalfunctions import is_valid_class


class Signing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def removesign(self, name, raidname):
        await self.bot.db.execute('''
        DELETE FROM signs
        WHERE raid = $1 AND name = $2''', raidname, name)

    @commands.command()
    async def sign(self, ctx, raidname, playerclass):
        name = ctx.message.author.display_name
        user_id = ctx.message.author.id
        raidname = raidname.upper()

        success, playerclass = is_valid_class(playerclass)

        if success is False:
            return

        await self.removesign(name, raidname)

        await self.bot.db.execute('''
        INSERT INTO signs (raid, name, class, id)
        VALUES ($1, $2, $3, $4)''', raidname, name, playerclass, user_id)

        # await ctx.message.delete(delay=3)

    @commands.command()
    async def decline(self, ctx, raidname):
        name = ctx.message.author.display_name
        user_id = ctx.message.author.id
        raidname = raidname.upper()
        playerclass = "Declined"

        await self.removesign(name, raidname)

        await self.bot.db.execute('''
        INSERT INTO signs (raid, name, class, id)
        VALUES ($1, $2, $3, $4)''', raidname, name, playerclass, user_id)

        # await ctx.message.delete(delay=3)

    @commands.command()
    async def addplayer(self, ctx, name, raidname, playerclass, user_id):
        raidname = raidname.upper()
        success, playerclass = is_valid_class(playerclass)

        user_id = int(user_id)

        if success is False:
            return

        await self.bot.db.execute('''
        INSERT INTO signs (raid, name, class, id)
        VALUES ($1, $2, $3, $4)''', raidname, name, playerclass, user_id)


def setup(bot):
    bot.add_cog(Signing(bot))

