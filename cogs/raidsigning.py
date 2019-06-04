import discord
import asyncio
import asyncpg

from discord.ext import commands
from raidhandling import Raid
from globalfunctions import is_valid_class, getlevel, getraidid


class Signing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raids = Raid(bot)

    @commands.command()
    async def getuserid(self, ctx, name):

        members = ctx.guild.members

        for member in members:
            if member.display_name == name:
                return member.id

        await ctx.send('No member found')

    async def removesign(self, player_id, raid_id):

        await self.bot.db.execute('''
        DELETE FROM sign
        WHERE raidid = $1 AND playerid = $2''', raid_id, player_id)

    @commands.command()
    async def sign(self, ctx, raidname, playerclass=None):

        if playerclass is not None:

            success, playerclass = await is_valid_class(playerclass)

            if success is False:
                return

        player_id = ctx.message.author.id
        raidname = raidname.upper()
        guild_id = ctx.guild.id

        row = await getraidid(self.bot.db, guild_id, raidname)

        if row is None:
            await ctx.send("No such raid exists")
            return

        await self.removesign(player_id, row['id'])

        await self.bot.db.execute('''
        INSERT INTO sign (playerid, raidid, playerclass)
        VALUES ($1, $2, $3) ON CONFLICT DO NOTHING''', player_id, row['id'], playerclass)

        # await ctx.invoke(self.raids.comp, ctx, raidname)

        # await ctx.message.delete(delay=3)

    # Add optional parameter so method removeplayer is easier to implement
    @commands.command()
    async def decline(self, ctx, raidname):
        playerclass = "Declined"
        await ctx.invoke(self.sign, raidname, playerclass)

        # await ctx.message.delete(delay=3)

    # Not done
    @commands.command()
    async def addplayer(self, ctx, name, raidname, playerclass, user_id=None):

        success, playerclass = await is_valid_class(playerclass)

        if success is False:
            return

        row = await self.getuserid(name)

        # User is in player table and has id there
        if row is not None:
            user_id = row

        if user_id is not None:
            user_id = int(user_id)

        # No id given and user is not in player table
        if row is None and user_id is None:
            await ctx.send("Give discord ID")
            return

        # Id is given, but user is not in player table -> add user
        if row is None and user_id is not None:
            user_id = int(user_id)
            await self.bot.db.execute('''
            INSERT into player(id, name) VALUES ($1, $2)
            ''', user_id, name)

        raidname = raidname.upper()

        await self.removesign(user_id, raidname)

        await self.bot.db.execute('''
        INSERT INTO sign (playerid, raidname, playerclass)
        VALUES ($1, $2, $3)''', user_id, raidname, playerclass)

    # Not done
    @commands.command()
    async def removeplayer(self, ctx, name, raidname, user_id=None):
        playerclass = "Declined"
        await ctx.invoke(self.addplayer, name, raidname, playerclass, user_id)

    # Not done/testing
    @commands.is_owner()
    @commands.command()
    async def removefromdb(self, ctx, user_id):
        user_id = int(user_id)
        await self.bot.db.execute('''
        DELETE FROM player
        WHERE id = $1''', user_id)


def setup(bot):
    bot.add_cog(Signing(bot))
