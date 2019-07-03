import discord
import asyncio
import asyncpg

from globalfunctions import is_valid_class
from discord.ext import commands


class Membership(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            await ctx.send("Invalid class")
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
            await ctx.send("Invalid class")
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
    bot.add_cog(Membership(bot))
