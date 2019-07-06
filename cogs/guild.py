import discord
import asyncio
import asyncpg

from discord.ext import commands
from utils.permissions import default_role_perms_comp_raid, bot_perms


class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def compchannel(self, guild_id, channel_id):
        await self.bot.db.execute('''
        UPDATE guild
        SET compchannel = $1
        WHERE id = $2''', channel_id, guild_id)

    async def raidchannel(self, guild_id, channel_id):
        await self.bot.db.execute('''
        UPDATE guild
        SET raidchannel = $1
        WHERE id = $2''', channel_id, guild_id)

    @commands.command()
    async def addraidchannel(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        exists = await self.bot.db.fetchval('''
        SELECT EXISTS (SELECT raidchannel FROM guild
        WHERE id = $1
        LIMIT 1)''', guild_id)

        if exists is True:
            return

        overwrites_raids_comps = {guild.default_role: default_role_perms_comp_raid,
                                  guild.me: bot_perms}

        raid_channel = await guild.create_text_channel('Raids', overwrites=overwrites_raids_comps)

        await self.raidchannel(guild_id, raid_channel)

    @commands.command()
    async def addcompchannel(self, ctx):
        guild = ctx.guild
        guild_id = guild.id

        exists = await self.bot.db.fetchval('''
        SELECT EXISTS (SELECT compchannel FROM guild
        WHERE id = $1
        LIMIT 1)''', guild_id)

        if exists is True:
            return

        overwrites_raids_comps = {guild.default_role: default_role_perms_comp_raid,
                                  guild.me: bot_perms}

        comp_channel = await guild.create_text_channel('Comps', overwrites=overwrites_raids_comps)

        await self.compchannel(guild_id, comp_channel)


def setup(bot):
    bot.add_cog(Guild(bot))
