import discord
import asyncio
import asyncpg

from discord.ext import commands
from raidhandling import Raid
from globalfunctions import is_valid_class, sign_player, get_raidid


class Signing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raids = Raid(bot)

    @commands.command()
    async def sign(self, ctx, raidname, playerclass, player_id=None):
        playerclass = await is_valid_class(playerclass)

        if playerclass is None:
            await ctx.send("Invalid class")
            return

        if player_id is None:
            player_id = ctx.message.author.id

        raidname = raidname.upper()
        guild_id = ctx.guild.id

        raid_id = await get_raidid(self.bot.db, guild_id, raidname)

        if raid_id is None:
            await ctx.send("Raid not found")
            return

        if not (await sign_player(self.bot.db, player_id, raid_id, playerclass)):
            await ctx.send("No player")

        # await ctx.invoke(self.raids.comp, ctx, raidname)

        # await ctx.message.delete(delay=3)

    @commands.command()
    async def decline(self, ctx, raidname):
        playerclass = "Declined"
        await ctx.invoke(self.sign, raidname, playerclass)

        # await ctx.message.delete(delay=3)

    @commands.command()
    async def addplayer(self, ctx, name, raidname, playerclass):
        member = await ctx.guild.get_member_named(name)

        # No id found
        if member is None:
            await ctx.send("No player found")
            return

        await ctx.invoke(self.sign, raidname, playerclass, member.id)

    @commands.command()
    async def removeplayer(self, ctx, name, raidname):
        playerclass = "Declined"
        await ctx.invoke(self.addplayer, name, raidname, playerclass)

    # Not done/testing
    @commands.is_owner()
    @commands.command()
    async def clearm(self, ctx):
        await self.bot.db.execute('''
        DELETE FROM membership
        WHERE playerid = $1''', ctx.message.author.id)

    @commands.command()
    async def clearp(self, ctx):
        await self.bot.db.execute('''
        DELETE FROM player
        WHERE id = $1''', ctx.message.author.id)

    @commands.command()
    async def clears(self, ctx):
        await self.bot.db.execute('''
        DELETE FROM sign
        WHERE playerid = $1''', ctx.message.author.id)

    @commands.command()
    async def cleara(self, ctx):
        await ctx.invoke(self.clearm)
        await ctx.invoke(self.clears)
        await ctx.invoke(self.clearp)


def setup(bot):
    bot.add_cog(Signing(bot))
