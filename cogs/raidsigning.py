import discord
import asyncio
import asyncpg

from discord.ext import commands
from raidhandling import Raids
from globalfunctions import is_valid_class


class Signing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raids = Raids(bot)

    async def getuserid(self, name):

        row = await self.bot.db.fetchrow('''
        SELECT player.id
        FROM player
        WHERE player.name = $1''', name)

        if row is None:
            return None
        else:
            return row['id']

    async def removesign(self, playerid, raidname):
        await self.bot.db.execute('''
        DELETE FROM sign
        WHERE raidname = $1 AND playerid = $2''', raidname, playerid)

    @commands.command()
    async def sign(self, ctx, raidname, playerclass):
        success, playerclass = is_valid_class(playerclass)

        if success is False:
            return

        name = ctx.message.author.display_name
        playerid = ctx.message.author.id
        raidname = raidname.upper()

        await self.bot.db.execute('''
        INSERT INTO player (id, name) VALUES ($1, $2)
        ON CONFLICT DO NOTHING''', playerid, name)

        await self.removesign(playerid, raidname)

        await self.bot.db.execute('''
        INSERT INTO sign (playerid, raidname, playerclass)
        VALUES ($1, $2, $3)''', playerid, raidname, playerclass)

        # await ctx.invoke(self.raids.comp, ctx, raidname)

        # await ctx.message.delete(delay=3)

    # Add optional parameter so method removeplayer is easier to implement
    @commands.command()
    async def decline(self, ctx, raidname):
        name = ctx.message.author.display_name
        playerid = ctx.message.author.id
        raidname = raidname.upper()
        # Add this to method (playerclass)
        playerclass = "Declined"

        await self.bot.db.execute('''
        INSERT INTO player (id, name) VALUES ($1, $2)
        ON CONFLICT DO NOTHING''', playerid, name)

        await self.removesign(playerid, raidname)

        # Separate this into method
        await self.bot.db.execute('''
        INSERT INTO sign (playerid, raidname, playerclass)
        VALUES ($1, $2, $3)''', playerid, raidname, playerclass)

        # await ctx.message.delete(delay=3)

    @commands.command()
    async def addplayer(self, ctx, name, raidname, playerclass, user_id=None):

        success, playerclass = is_valid_class(playerclass)

        if success is False:
            return

        row = await self.getuserid(name)
        # No id given and user is not in player table
        if user_id is None and row is None:
            await ctx.send("Give discord ID")
            return

        # Id is given, but user is not in player table -> add user
        if row is None and user_id is not None:
            user_id = int(user_id)
            await self.bot.db.execute('''
            INSERT into player(id, name) VALUES ($1, $2)
            ''', user_id, name)

        # User is in player table and has id there
        if row is not None and user_id is not None:
            user_id = int(user_id)

        raidname = raidname.upper()

        await self.removesign(user_id, raidname)

        await self.bot.db.execute('''
        INSERT INTO sign (playerid, raidname, playerclass)
        VALUES ($1, $2, $3)''', user_id, raidname, playerclass )

    @commands.command()
    async def removeplayer(self, ctx, name, raidname, user_id=None):
        playerclass = "Declined"
        await ctx.invoke(self.addplayer, name, raidname, playerclass, user_id)

    @commands.is_owner()
    @commands.command()
    async def removefromdb(self, ctx, user_id):
        user_id = int(user_id)
        await self.bot.db.execute('''
        DELETE FROM player
        WHERE id = $1''', user_id)


def setup(bot):
    bot.add_cog(Signing(bot))

