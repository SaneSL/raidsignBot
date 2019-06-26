import discord
import asyncio
import asyncpg

from discord.ext import commands
from globalfunctions import has_any_permission


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
    @has_any_permission(administrator=True, manage_guild=True)
    async def testio(self, ctx):
        channel = ctx.channel
        print("XD")

def setup(bot):
    bot.add_cog(Misc(bot))
