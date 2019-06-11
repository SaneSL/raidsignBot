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

    async def addself(self, player_id):
        await self.bot.db.execute('''
        INSERT INTO player
        VALUES ($1)
        ON CONFLICT DO NOTHING''', player_id)

    @commands.command()
    async def addmain(self, ctx, playerclass):
        player_id = ctx.message.author.id
        guild_id = ctx.guild.id

        await self.addself(player_id)

        playerclass = await is_valid_class(playerclass)

        if playerclass is None:
            await ctx.send("Check class syntax")
            return

        await self.bot.db.execute('''
        INSERT INTO membership (guildid, playerid, main)
        VALUES ($1, $2, $3)
        ON CONFLICT (guildid, playerid) DO UPDATE
        SET main = $3
        ''', guild_id, player_id, playerclass)

    @commands.command()
    async def addalt(self, ctx, playerclass):
        player_id = ctx.message.author.id
        guild_id = ctx.guild.id

        await self.addself(player_id)

        playerclass = await is_valid_class(playerclass)

        if playerclass is None:
            await ctx.send("Check class syntax")
            return

        await self.bot.db.execute('''
        INSERT INTO membership (guildid, playerid, alt)
        VALUES ($1, $2, $3)
        ON CONFLICT (guildid, playerid) DO UPDATE
        SET alt = $3
        ''', guild_id, player_id, playerclass)

    @commands.command()
    async def autosign(self, ctx):
        guild = ctx.guild
        member = ctx.author

        role = discord.utils.get(guild.roles, name='AutoSign')

        if role is None:
            return

        if role in member.roles:
            await member.remove_roles(role, reason="Remove auto sign role")
            return

        await member.add_roles(role, reason='Auto sign role')


def setup(bot):
    bot.add_cog(Misc(bot))
