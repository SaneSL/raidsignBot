import discord
import asyncio
import asyncpg

from discord.ext import commands
from utils.permissions import default_role_perms_comp_raid, bot_perms, default_role_perms_commands
from utils import checks


class Guild(commands.Cog, name='Server'):
    """
    Includes some commands that are usefull if user deletes bot made channels or guild is somehow not stored in db.
    """

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def compchannel(con, guild_id, channel_id):
        await con.execute('''
        UPDATE guild
        SET compchannel = $1
        WHERE id = $2''', channel_id, guild_id)

    @staticmethod
    async def raidchannel(con, guild_id, channel_id):
        await con.execute('''
        UPDATE guild
        SET raidchannel = $1
        WHERE id = $2''', channel_id, guild_id)

    @staticmethod
    async def category(con, guild_id, category_id):
        await con.execute('''
        UPDATE guild
        SET category = $1
        WHERE id = $2''', category_id, guild_id)

    async def addraidchannel(self, con, guild, category):
        guild_id = guild.id
        topic = "This channel displays all available raids."

        overwrites_raids_comps = {guild.default_role: default_role_perms_comp_raid,
                                  guild.me: bot_perms}

        raid_channel = await guild.create_text_channel('raids', category=category,
                                                       overwrites=overwrites_raids_comps, topic=topic)
        await self.raidchannel(con, guild_id, raid_channel.id)

    async def addcompchannel(self, con, guild, category):
        guild_id = guild.id
        topic = "This channel displays all raids and their comps. Updated every 20 mins."

        overwrites_raids_comps = {guild.default_role: default_role_perms_comp_raid,
                                  guild.me: bot_perms}

        comp_channel = await guild.create_text_channel('comps', category=category,
                                                       overwrites=overwrites_raids_comps, topic=topic)

        await self.compchannel(con, guild_id, comp_channel.id)

    async def addcategory(self, con, guild, category_id, raid_channel_id, comp_channel_id):
        guild_id = guild.id

        # Check if channel exists in db and not guild
        if category_id is not None:
            category = guild.get_channel(category_id)
            if category is None:
                category = await guild.create_category('raidsign')
                await self.category(con, guild_id, category.id)
        # Category not in DB, create new one and a cmd-channel
        else:
            category = await guild.create_category('raidsign')
            await self.category(con, guild_id, category.id)

            topic_bc = "You can use bot-commands here or any other channel. If you already have a channel for " \
                       "this purpose or don't want to use this channel, feel free to delete it."

            overwrites_bot_commands = {guild.default_role: default_role_perms_commands,
                                       guild.me: bot_perms}

            cmd_channel = await guild.create_text_channel('bot-commands', overwrites=overwrites_bot_commands
                                                          , category=category, topic=topic_bc)

        # Check if channel exists in db and not guild
        if raid_channel_id is not None:
            raid_channel = guild.get_channel(raid_channel_id)
            if raid_channel is None:
                await self.addraidchannel(con, guild, category)
            else:
                await raid_channel.edit(category=category)
        else:
            await self.addraidchannel(con, guild, category)

        # Check if channel exists in db and not guild
        if comp_channel_id is not None:
            comp_channel = guild.get_channel(comp_channel_id)
            if comp_channel is None:
                await self.addcompchannel(con, guild, category)
            else:
                await comp_channel.edit(category=category)
        else:
            await self.addcompchannel(con, guild, category)

    async def add_bot_channels(self, guild):
        guild_id = guild.id

        async with self.bot.pool.acquire() as con:
            guild_info = await con.fetchrow("""
            SELECT raidchannel, compchannel, category
            FROM guild
            WHERE id = $1""", guild_id)

            if guild_info is None:
                return

            await self.addcategory(con, guild, guild_info['category'], guild_info['raidchannel'],
                                   guild_info['compchannel'])

        await self.bot.pool.release(con)

    @commands.cooldown(1, 300, commands.BucketType.guild)
    @checks.has_any_permission(administrator=True, manage_guild=True)
    @commands.command(description="Readds bot made channels incase deleted.", help="Administrator, manage server",
                      brief='{"examples":[], "cd":"300"}')
    async def addchannels(self, ctx):
        await self.add_bot_channels(ctx.guild)

    @commands.cooldown(1, 600, commands.BucketType.guild)
    @commands.command(description="Adds server to the db. This command shouldn't be needed.",
                      brief='{"examples":[], "cd":"600"')
    async def addserver(self, ctx):
        guild_id = ctx.guild.id
        await self.bot.pool.execute('''
        INSERT INTO guild (id) VALUES ($1) ON CONFLICT DO NOTHING''', guild_id)


def setup(bot):
    bot.add_cog(Guild(bot))
