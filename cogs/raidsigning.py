import discord
import asyncio
import asyncpg

from discord.ext import commands
from raidhandling import Raid
from globalfunctions import is_valid_class, getlevel, getraidid, getuserid


class Signing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raids = Raid(bot)

    async def removesign(self, player_id, raid_id):

        await self.bot.db.execute('''
        DELETE FROM sign
        WHERE raidid = $1 AND playerid = $2''', raid_id, player_id)

    @commands.command()
    async def sign(self, ctx, raidname, playerclass=None, player_id=None):

        print(ctx.message.author)

        if playerclass is not None:

            success, playerclass = await is_valid_class(playerclass)

            if success is False:
                return

        if player_id is None:
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

    @commands.command()
    async def decline(self, ctx, raidname):
        playerclass = "Declined"
        await ctx.invoke(self.sign, raidname, playerclass)

        # await ctx.message.delete(delay=3)

    @commands.command()
    async def addplayer(self, ctx, name, raidname, playerclass):

        members = ctx.guild.members

        player_id = await getuserid(members, name)

        # No id found
        if player_id == -1:
            await ctx.send("No player found")
            return

        await ctx.invoke(self.sign, raidname, playerclass, player_id)

    @commands.command()
    async def removeplayer(self, ctx, name, raidname):
        playerclass = "Declined"
        await ctx.invoke(self.addplayer, name, raidname, playerclass)

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
