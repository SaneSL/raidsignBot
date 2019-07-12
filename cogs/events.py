import discord

from discord.ext import commands
from utils.globalfunctions import clear_guild_from_db, clear_all_signs, null_category,\
    null_raid_channel, null_comp_channel, get_raid_channel_id
from utils.permissions import default_role_perms_commands, default_role_perms_comp_raid, bot_perms


class Botevents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Remove transaction?
    @commands.command()
    async def add_reacted_signs(self, ctx):
        async with self.bot.db.acquire() as con:
            async with con.transaction():
                raids = await self.bot.db.fetch('''
                SELECT id
                FROM raid
                WHERE guildid = $1''', ctx.guild.id)

                if raids is None:
                    await self.bot.db.release(con)
                    return

                raid_channel_id = await get_raid_channel_id(self.bot.db, ctx.guild.id)

                if raid_channel_id is None:
                    await self.bot.db.release(con)
                    return

                raid_channel = ctx.guild.get_channel(raid_channel_id)

                players = await con.fetch('''
                SELECT playerid, main, alt
                FROM membership
                WHERE guildid = $1''', ctx.guild.id)

                # Maybe tuple as key (playerid, guildid) value (classes) if you want to handle all classes at once,
                # prolly not good though

                player_dict = {}

                for player in players:
                    player_dict[player['playerid']] = (player['main'], player['alt'])

                for raid in raids:
                    msg = await raid_channel.fetch_message(raid['id'])
                    reactions = msg.reactions
                    for reaction in reactions:
                        if reaction.emoji in {'\U0001f1fe', '\U0001f1f3', '\U0001f1e6'}:
                            async for user in reaction.users():
                                tuple_value = player_dict.get(user.id)

                                if tuple_value is None:
                                    continue

                                elif reaction.emoji == '\U0001f1fe':
                                    playerclass = tuple_value[0]

                                elif reaction.emoji == '\U0001f1f3':
                                    playerclass = 'Declined'

                                else:
                                    playerclass = tuple_value[1]

                                if playerclass is None:
                                    continue

                                await con.execute('''
                                INSERT INTO sign (playerid, raidid, playerclass)
                                VALUES ($1, $2, $3)
                                ON CONFLICT (playerid, raidid) DO UPDATE
                                SET playerclass = $3''', user.id, raid['id'], playerclass)

        await self.bot.db.release(con)

    async def get_guilds_no_setup_channels(self):
        guilds = await self.bot.db.fetch('''
        SELECT id
        FROM guild
        WHERE category is NULL AND raidchannel is NULL and compchannel is NULL''')

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

        guild_cog = self.bot.get_cog('Guild')

        overwrites_bot_commads = {guild.default_role: default_role_perms_commands,
                                  guild.me: bot_perms}

        overwrites_raids_comps = {guild.default_role: default_role_perms_comp_raid,
                                  guild.me: bot_perms}

        category_name = "Raidsign"
        category = await guild.create_category(category_name)
        await guild.create_text_channel('Bot-commands', overwrites=overwrites_bot_commads, category=category)
        raid_channel = await guild.create_text_channel('Raids', overwrites=overwrites_raids_comps, category=category)
        comp_channel = await guild.create_text_channel('Comps', overwrites=overwrites_raids_comps, category=category)

        await guild_cog.category(guild.id, category.id)
        await guild_cog.raidchannel(guild.id, raid_channel.id)
        await guild_cog.compchannel(guild.id, comp_channel.id)

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

        if clear_list:
            await clear_guild_from_db(self.bot.db, clear_list)

        guild_objects = await self.get_guilds_no_setup_channels()

        if guild_objects is None:
            return

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

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        channel_id = channel.id

        guild_info = await self.bot.db.fetchrow('''
        SELECT raidchannel, compchannel, category
        FROM guild
        WHERE id = $1''', guild.id)

        if guild_info is None:
            return

        raid_channel_id = guild_info['raidchannel']
        comp_channel_id = guild_info['compchannel']
        category_id = guild_info['category']

        if channel_id in {raid_channel_id, comp_channel_id, category_id}:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):
                if entry.target.id in {raid_channel_id, comp_channel_id, category_id}:
                    await entry.user.send("You just deleted important channel")
                    pass

            if channel_id == raid_channel_id:
                await clear_all_signs(self.bot.db, guild.id)
                await null_raid_channel(self.bot.db, guild.id)
            elif channel_id == comp_channel_id:
                # Tag the user who deleted the channel and ask them to create new channel with x command
                await null_comp_channel(self.bot.db, guild.id)
            elif channel_id == category_id:
                await null_category(self.bot.db, guild.id)

    @commands.command()
    async def addguild(self, ctx):
        await self.addguildtodb(ctx.guild)


def setup(bot):
    bot.add_cog(Botevents(bot))
