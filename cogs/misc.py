import discord
import asyncio
import asyncpg

from discord.ext import commands
from globalfunctions import is_valid_class


class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        author = ctx.message.author

        embed = discord.Embed(colour=discord.Colour.dark_orange())

        s = "Sign to raids"

        embed.set_author(name='Help')
        embed.add_field(name='!sign', value=s, inline=False)

        await author.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def clear(self, ctx, amount=2):
        await ctx.channel.purge(limit=amount)

    @commands.command()
    async def addclass(self, ctx, playerclass):
        playerid = ctx.message.author.id

        success, playerclass = await is_valid_class(playerclass)

        if success is False:
            await ctx.send("Check class syntax")
            return

        await self.bot.db.execute('''
        INSERT INTO player (id, class) VALUES ($1, $2)
        ON CONFLICT DO NOTHING''', playerid, playerclass)


def setup(bot):
    bot.add_cog(Misc(bot))
