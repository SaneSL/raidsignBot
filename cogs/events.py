import discord

from discord.ext import commands
from utils.globalfunctions import clear_guild_from_db
from utils.permissions import default_role_perms_commands, default_role_perms_comp_raid, bot_perms


class Botevents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_guilds(self):
        guilds = await self.bot.db.fetch('''
        SELECT id
        FROM guild
        WHERE raidchannel IS NULL OR compchannel IS NULL''')

        guild_obj_list = []

        for guild in guilds:
            guild_object = self.bot.get_guild(guild['id'])
            if guild_object is not None:
                guild_obj_list.append(guild_object)

        if not guild_obj_list:
            return None
        else:
            return guild_obj_list

    async def addguildtodb(self, guild):
        guild_id = guild.id

        await self.bot.db.execute('''
        INSERT INTO guild (id) VALUES ($1) ON CONFLICT DO NOTHING''', guild_id)

    async def setup_channels(self, guild):
        overwrites_bot_commads = {guild.default_role: default_role_perms_commands,
                                  guild.me: bot_perms}

        overwrites_raids_comps = {guild.default_role: default_role_perms_comp_raid,
                                  guild.me: bot_perms}

        category_name = "Raidsign"
        category = await guild.create_category(category_name)
        await guild.create_text_channel('Bot-commands',overwrites=overwrites_bot_commads, category=category)
        await guild.create_text_channel('Raids', overwrites= overwrites_raids_comps, category=category)
        await guild.create_text_channel('Comps', overwrites=overwrites_raids_comps, category=category)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot is ready.')
        for guild in self.bot.guilds:
            await self.addguildtodb(guild)

        guilds = await self.bot.db.fetch('''
        SELECT id
        FROM guild''')

        guild_id_list = []
        bot_guilds = self.bot.guilds

        for guild in guilds:
            guild_id_list.append(guild['id'])

        bot_guild_ids = []

        for guild in bot_guilds:
            bot_guild_ids.append(guild.id)

        clear_list = [x for x in guild_id_list if x not in bot_guild_ids]

        if not clear_list:
            return

        await clear_guild_from_db(self.bot.db, clear_list)

        guild_objects = await self.get_guilds()

        for guild in guild_objects:
            await self.setup_channels(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.addguildtodb(guild)
        await self.setup_channels(guild)

    @commands.Cog.listener()
    async def on_guild_leave(self, guild):
        guild_id = [guild.id]
        await clear_guild_from_db(self.bot.db, guild_id)

    @commands.command()
    async def addguild(self, ctx):
        await self.addguildtodb(ctx.guild)


def setup(bot):
    bot.add_cog(Botevents(bot))
