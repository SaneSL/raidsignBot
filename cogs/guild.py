import discord
import asyncio
import asyncpg

from discord.ext import commands
from utils.permissions import default_role_perms_comp_raid, bot_perms
from utils.globalfunctions import get_comp_channel_id, get_raid_channel_id, get_category_id


class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def compchannel(self, guild_id, channel_id):
        await self.bot.pool.execute('''
        UPDATE guild
        SET compchannel = $1
        WHERE id = $2''', channel_id, guild_id)

    async def raidchannel(self, guild_id, channel_id):
        await self.bot.pool.execute('''
        UPDATE guild
        SET raidchannel = $1
        WHERE id = $2''', channel_id, guild_id)

    async def category(self, guild_id, category_id):
        await self.bot.pool.execute('''
        UPDATE guild
        SET category = $1
        WHERE id = $2''', category_id, guild_id)

    async def addraidchannel(self, guild, raid_channel_id, category_id):
        guild_id = guild.id

        # Check if channel exists in db and guild
        if raid_channel_id is not None:
            raid_channel = guild.get_channel(raid_channel_id)
            if raid_channel is not None:
                return

        if category_id is None:
            return

        category_channel = guild.get_channel(category_id)

        if category_channel is None:
            return

        overwrites_raids_comps = {guild.default_role: default_role_perms_comp_raid,
                                  guild.me: bot_perms}

        raid_channel = await guild.create_text_channel('Raids', category=category_channel,
                                                       overwrites=overwrites_raids_comps)

        await self.raidchannel(guild_id, raid_channel.id)

    async def addcompchannel(self, guild, comp_channel_id, category_id):
        guild_id = guild.id

        # Check if channel exists in db and guild
        if comp_channel_id is not None:
            comp_channel = guild.get_channel(comp_channel_id)
            if comp_channel is not None:
                return

        if category_id is None:
            return

        category_channel = guild.get_channel(category_id)

        if category_channel is None:
            return

        overwrites_raids_comps = {guild.default_role: default_role_perms_comp_raid,
                                  guild.me: bot_perms}

        comp_channel = await guild.create_text_channel('Comps', category=category_channel,
                                                       overwrites=overwrites_raids_comps)

        await self.compchannel(guild_id, comp_channel.id)

    async def addcategory(self, guild, category_id, raid_channel_id, comp_channel_id):
        guild_id = guild.id

        # Check if channel exists in db and guild
        if category_id is not None:
            category = guild.get_channel(category_id)
            if category is not None:
                return

        category = await guild.create_category('Raidsign')

        # Check if channel exists in db and guild
        if raid_channel_id is not None:
            raid_channel = guild.get_channel(raid_channel_id)
            if raid_channel is not None:
                await raid_channel.edit(category=category)

        # Check if channel exists in db and guild
        if comp_channel_id is not None:
            comp_channel = guild.get_channel(comp_channel_id)
            if comp_channel is not None:
                await comp_channel.edit(category=category)

        await self.category(guild_id, category.id)

    @commands.command()
    async def addchannels(self, ctx):
        guild_info = self.bot.pool.fetchrow("""
        SELECT raidchannel, compchannel, category
        FROM guild
        WHERE id = $1""", ctx.guild.id)

        if guild_info is None:
            return

        await self.addcategory(ctx.guild, guild_info['category'], guild_info['raidchannel'], guild_info['compchannel'])
        await self.addraidchannel(ctx.guild, guild_info['raidchannel'], guild_info['category'])
        await self.addcompchannel(ctx.guild, guild_info['compchannel'], guild_info['category'])


def setup(bot):
    bot.add_cog(Guild(bot))
