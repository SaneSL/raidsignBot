import discord
import asyncio
import asyncpg

from discord.ext import commands


class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def compchan(self, ctx, channel_id):
        guild_id = ctx.guild.id
        channel_id = int(channel_id)

        await self.bot.db.execute('''
        UPDATE guild
        SET compchannel = $1
        WHERE id = $2''', channel_id, guild_id)

    @commands.command()
    async def raidchan(self, ctx, channel_id):
        guild_id = ctx.guild.id
        channel_id = int(channel_id)

        await self.bot.db.execute('''
        UPDATE guild
        SET raidchannel = $1
        WHERE id = $2''', channel_id, guild_id)


def setup(bot):
    bot.add_cog(Guild(bot))
