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
    async def addself(self, ctx):
        player_id = ctx.message.author.id

        await self.bot.db.execute('''
        INSERT INTO player
        VALUES ($1)
        ON CONFLICT DO NOTHING''', player_id)

    @commands.command()
    async def addclass(self, ctx, playerclass):
        player_id = ctx.message.author.id
        guild_id = ctx.guild.id

        success, playerclass = await is_valid_class(playerclass)

        if success is False:
            await ctx.send("Check class syntax")
            return

        await self.bot.db.execute('''
        INSERT INTO membership (guildid, playerid, class)
        VALUES ($1, $2, $3)
        ON CONFLICT (guildid, playerid) DO UPDATE
        SET class = $3
        ''', guild_id, player_id, playerclass)


def setup(bot):
    bot.add_cog(Misc(bot))
