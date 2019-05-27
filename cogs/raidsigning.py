import discord
import asyncio
import asyncpg

from discord.ext import commands
from globalfunctions import is_valid_class


class Signing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        # await ctx.message.delete(delay=3)

    # Add optional parameter so method removeplayer is easier to implement
    @commands.command()
    async def decline(self, ctx, raidname):
        name = ctx.message.author.display_name
        playerid = ctx.message.author.id
        raidname = raidname.upper()
        playerclass = "Declined"

        await self.bot.db.execute('''
        INSERT INTO player (id, name) VALUES ($1, $2)
        ON CONFLICT DO NOTHING''', playerid, name)

        await self.removesign(playerid, raidname)

        await self.bot.db.execute('''
        INSERT INTO sign (playerid, raidname, playerclass)
        VALUES ($1, $2, $3)''', playerid, raidname, playerclass)

        # await ctx.message.delete(delay=3)

    # If ID is given, but player is not in players and the id is valid and the player is present in the discord server
    # Say if player can't be added based on name, only if player hasn't signed before.
    @commands.command()
    async def addplayer(self, ctx, name, raidname, playerclass, user_id=None):
        success, playerclass = is_valid_class(playerclass)

        if success is False:
            return

        if user_id is None:

            row = await self.bot.db.fetchrow('''
            SELECT player.id
            FROM player
            WHERE player.name = $1''', name)

            if row is None:
                return
            else:
                user_id = row['id']
        else:
            user_id = int(user_id)

        raidname = raidname.upper()

        await self.bot.db.execute('''
        INSERT INTO sign (playerid, raidname, playerclass)
        VALUES ($1, $2, $3)''', user_id, raidname, playerclass )


def setup(bot):
    bot.add_cog(Signing(bot))

